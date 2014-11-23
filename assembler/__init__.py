import re
from .state import State
from .expression import ConstantExpression

__all__ = ["assemble"]

_const_parser = None

def _evaluate_d(expression : str, state : State) -> int:

    value = _get_register(expression) or state.GetLabelAddress(expression)

    if not value:
        value = _const_parser.Evaluate(expression)

    return "{:0>9b}".format(value)

def _evaluate_s(expression : str, state : State) -> str:

    value = _get_register(expression) or state.GetLabelAddress(expression)

    if not value:
        value = _const_parser.Evaluate(expression)

    if value > 0x1FF:
        raise AssemblerError(state.LineNumber, "s-field expression evaluated to a value greater than $1FF.")

    return "{:0>9b}".format(value)

def _get_register(name : str) -> int:
    return None if name not in lang.registers else lang.registers[name]

def assemble(source, binary_format="binary", hub_offset=0, syntax_version=1):
    global _const_parser

    state = State()
    pending = []
    output = []

    if binary_format != "raw":
        state.HubAddress = 0x10
    else:
        state.HubAddress = int(hub_offset)

    _const_parser = ConstantExpression(state)

    # PASS 1
    for line in source:
        state.LineNumber += 1
        
        if "'" in line:
            line = line[:line.index("'")]     # remove comments
        
        if line == "" or str.isspace(line):     # ignore empty lines
            continue
        
        line = line.upper()

        parts = line.split(maxsplit=1)

        label = ""
        directive = ""
        cond = ""
        opcode = ""
        parameters = ""

        try:
            if parts[0] not in lang.reserved_words:
                label = parts[0]
                parts = parts[1].split(maxsplit=1) if len(parts) == 2 else []

            if parts and parts[0] in lang.directives:
                directive = parts[0]
                parameters = parts[1] if len(parts) == 2 else ""
                parts = []

            if parts and parts[0] in lang.conditions:
                cond = parts[0]
                parts = parts[1].split(maxsplit=1) if len(parts) == 2 else []

            if parts and parts[0] in lang.instructions:
                opcode = parts[0]
                parameters = parts[1] if len(parts) == 2 else ""
                parts = []

            if parts and parts[0] in lang.datatypes:
                opcode = parts[0]
                parameters = parts[1] if len(parts) == 2 else ""
                parts = []

            if label != "":
                if directive in ("ORG", "FIT"):
                    raise AssemblerError(state.LineNumber, "Labels are not allowed for ORG or FIT.")
         
                if not state.AddLabel(label):
                    raise AssemblerError(state.LineNumber, "Could not add label '{}'".format(label))

            if directive != "":
                if directive == "ORG":
                    if parameters == "":
                        state.ORG()
                    else:
                        state.ORG(_const_parser.Evaluate(parameteters))

                elif directive == "FIT":
                    fit = (parameters == "") and state.FIT() or state.FIT(_const_parser.Evaluate(parameters))

                    if not fit:
                        raise AssemblerError(state.LineNumber, "It doesn't FIT!")

                elif directive == "RES":
                    state.FixLabelAddresses()

                    if parameters == "":
                        state.RES()
                    else:
                        state.RES(_const_parser.Evaluate(parameters))

                else:
                    raise AssemblerError(state.LineNumber, "Unrecognized directive!")
        
            if opcode != "":
                state.FixLabelAddresses()

                pending.append((cond, opcode, parameters.strip(), state.LineNumber, state.CogAddress, state.HubAddress, line))

                state.CogAddress += 1
                state.HubAddress += 1


            if directive == "" and opcode == "" and label == "":
                raise AssemblerError(state.LineNumber, "unrecognized text: {}".format(line))

            # print("> {0}".format(line.rstrip()))

        except AssemblerError as e:
            state.AddError(e)

    # print("Pass 2...")

    # PASS 2
    for line in pending:
        state.SetLineNumber(line[3])

        parameters = line[2]

        try:
            if line[1] in lang.datatypes:
                value = _const_parser.Evaluate(parameters)

                if line[1] == "BYTE":
                    if isinstance(value, list):
                        temp = value[0]
                        count = 8
                        for b in (value + [0,0,0])[1:]:
                            if b < 0: b += 0x100
                            temp += (b << count)
                            count += 8
                            if count == 32: break
                        value = temp
                    elif value < 0:
                        value += 0x100
                
                elif line[1] == "WORD":
                    if isinstance(value, list):
                        temp = value[0]
                        count = 16
                        for b in (value + [0])[1:]:
                            if b < 0: b += 0x10000
                            temp += (b << count)
                            count += 16
                            if count == 32: break
                        value = temp
                    elif value < 0:
                        value += 0x10000
                else:
                    if isinstance(value, list):
                        value = value[0]
                
                    if value < 0:
                        value += 0x100000000

                bits = "{:0>32b}".format(value)
            else:
                rules = lang.instructions[line[1]]

                bits = rules[0]

                if rules[5] and line[0]:
                    cond = lang.conditions[line[0]]
                    bits = bits[:10] + cond + bits[14:]

                if parameters:

                    wr_nr = False
                    effect = re.split("[\s\t\n,]+", parameters)[-1]

                    while effect in lang.effects:
                        if effect == "WZ":
                            if not line[1]:
                                raise AssemblerError(state.LineNumber, "WZ Not allowed!")

                            bits = bits[:6] + "1" + bits[7:]
                
                        elif effect == "WC":
                            if not line[2]:
                                raise AssemblerError(state.LineNumber, "WC Not allowed!")

                            bits = bits[:7] + "1" + bits[8:]
                
                        elif effect in ("WR", "NR"):
                            if not line[3]:
                                raise AssemblerError(state.LineNumber, "WR Not allowed!")
                            if wr_nr:
                                raise AssemblerError(state.LineNumber, "Cannot use NR and WR at the same time.")

                            bits = bits[:8] + ("1" if effect == "WR" else "0") + bits[9:]
                            wr_nr = True

                        parameters = parameters[:-3]

                        effect = parameters and re.split("[\s\t\n,]+", parameters)[-1] or ""

                    if parameters:
                        if "d" in bits and "s" in bits:
                            (d, s) = parameters.split(",")
                        elif "d" in bits:
                            d = parameters
                        elif "s" in bits:
                            s = parameters
                        else:
                            raise AssemblerError(state.LineNumber, "Unrecognized parameters: {}".format(parameters))
                
                        if "d" in bits:
                            d = d.strip()
                            d = _evaluate_d(d, state)
                            d_start = bits.index("d")
                            d_stop = bits.rindex("d")
                            bits = bits[:d_start] + d + bits[d_stop+1:]

                        if "s" in bits:
                            s = s.strip()
                            if s[0] == "#":
                                if not rules[4]:
                                    raise AssemblerError(state.LineNumber, "Source cannot have an immediate value.")

                                bits = bits[:9] + "1" + bits[10:]
                                s = s[1:]

                            s = _evaluate_s(s, state)
                            s_start = bits.index("s")
                            s_stop = bits.rindex("s")
                            bits = bits[:s_start] + s + bits[s_stop+1:]

                    if len(rules) == 7:
                        bits = rules[6](bits, line[2], state)

                bits = re.sub("[^01]", "0", bits)

            output.append(int(bits[24:32] + bits[16:24] + bits[8:16] + bits[0:8], 2))

            # hex = format(output[-1], "0>8x").upper()
            # print("[{}][{}] {}".format(bits, hex, line[5].rstrip()))
        
        except AssemblerError as e:
            state.AddError(e)


    if state.Errors:
        print("Errors Encountered:\n")

        for error in state.Errors:
            print("{: >3} : {}\n".format(error.LineNumber, error.Message))
    
        exit()


    data = bytearray()
        
    checksum = 0

    for v in output:
        data += bytearray.fromhex(format(v, "0>8x"))

    # Note: for "raw" format, all you get is the data.  So there is no additional processing.

    if binary_format in ("binary", "eeprom"):        
        spin_code = bytearray.fromhex("35 37 03 35   2C 00 00 00")
        
        pbase = 0x0010
        pcurr = pbase + len(data)
        vbase = pcurr + len(spin_code)
        dbase = vbase + 0x08
        dcurr = dbase + 0x04

        # Header (16 bytes)
        header  = bytearray(reversed(bytearray.fromhex(format(80000000, "0>8x"))))     # clkfreq   (4)
        header += bytearray([0x6F])                                                    # clkmode   (1)
        header += bytearray([0x00])                                                    # checksum  (1)
        header += bytearray(reversed(bytearray.fromhex(format(pbase, "0>4x"))))        # pbase     (2)
        header += bytearray(reversed(bytearray.fromhex(format(vbase, "0>4x"))))        # vbase     (2)
        header += bytearray(reversed(bytearray.fromhex(format(dbase, "0>4x"))))        # dbase     (2)
        header += bytearray(reversed(bytearray.fromhex(format(pcurr, "0>4x"))))        # pcurr     (2)
        header += bytearray(reversed(bytearray.fromhex(format(dcurr, "0>4x"))))        # dcurr     (2)
    
        data = header + data + spin_code

        # the modulus operators are due to Python's lack of a signed char type.
        # Same as "checksum = 0x14 - sum(data)".
        checksum = (sum(data) + 0xEC) % 256
        checksum = (256 - checksum) % 256
        data[0x05] = checksum

        if binary_format == "eeprom":
            data += bytearray([0xff, 0xff, 0xf9, 0xff] * 2)
            data += bytearray([0x00] * int(self.eepromSize - len(code)))

    return data
