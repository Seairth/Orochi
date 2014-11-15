# Orichi is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version. The
# software is distributed WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# the software.  If not, see <http://www.gnu.org/licenses/>.

from .state import State, AssemblerError

directives = ("ORG", "FIT", "RES")
effects = ("WC", "WZ", "WR", "NR")
datatypes = ("BYTE", "WORD", "LONG")

conditions = {}
conditions["IF_ALWAYS"]         = "1111"
conditions["IF_NEVER"]          = "0000"
conditions["IF_E"]              = "1010"
conditions["IF_NE"]             = "0101"
conditions["IF_A"]              = "0001"
conditions["IF_B"]              = "1100"
conditions["IF_AE"]             = "0011"
conditions["IF_BE"]             = "1110"
conditions["IF_C"]              = "1100"
conditions["IF_NC"]             = "0011"
conditions["IF_Z"]              = "1010"
conditions["IF_NZ"]             = "0101"
conditions["IF_C_EQ_Z"]         = "1001"
conditions["IF_C_NE_Z"]         = "0110"
conditions["IF_C_AND_Z"]        = "1000"
conditions["IF_C_AND_NZ"]       = "0100"
conditions["IF_NC_AND_Z"]       = "0010"
conditions["IF_NC_AND_NZ"]      = "0001"
conditions["IF_C_OR_Z"]         = "1110"
conditions["IF_C_OR_NZ"]        = "1101"
conditions["IF_NC_OR_Z"]        = "1011"
conditions["IF_NC_OR_NZ"]       = "0111"
conditions["IF_Z_EQ_C"]         = "1001"
conditions["IF_Z_NE_C"]         = "0110"
conditions["IF_Z_AND_C"]        = "1000"
conditions["IF_Z_AND_NC"]       = "0010"
conditions["IF_NZ_AND_C"]       = "0100"
conditions["IF_NZ_AND_NC"]      = "0001"
conditions["IF_Z_OR_C"]         = "1110"
conditions["IF_Z_OR_NC"]        = "1011"
conditions["IF_NZ_OR_C"]        = "1101"
conditions["IF_NZ_OR_NC"]       = "0111"

constants = {}
constants["TRUE"]               = -1            # 0xFFFFFFFF
constants["FALSE"]              = 0             # 0x00000000
constants["POSX"]               = 2147483647    # 0x7FFFFFFF
constants["NEGX"]               = -2147483648   # 0x80000000
constants["PI"]                 = 0x40490FDB    # IEEE 754 single-precision representation

registers = {}
registers["PAR"]                = 0x1F0
registers["CNT"]                = 0x1F1
registers["INA"]                = 0x1F2
registers["INB"]                = 0x1F3
registers["OUTA"]               = 0x1F4
registers["OUTB"]               = 0x1F5
registers["DIRA"]               = 0x1F6
registers["DIRB"]               = 0x1F7
registers["CTRA"]               = 0x1F8
registers["CTRB"]               = 0x1F9
registers["FRQA"]               = 0x1FA
registers["FRQB"]               = 0x1FB
registers["PHSA"]               = 0x1FC
registers["PHSB"]               = 0x1FD
registers["VCFG"]               = 0x1FE
registers["VSCL"]               = 0x1FF

def _fix_call(bits : str, parameters : str, state : State) -> str:
    if parameters[0] != "#":
        raise AssemblerError(state.LineNumber, "Cannot fix CALL. Parameters is: {}".format(parameter))

    label = parameters[1:]

    if label[0] == ":":
        label = state.CurrentLabel + label

    match = [l for l in state.Labels if l[0] == label]

    if not match:
        raise AssemblerError(state.LineNumber, "Cannot fix CALL. Label not found.")

    if len(match[0]) < 4:
        raise AssemblerError(state.LineNumber, "Cannot fix CALL. No matching '_ret' label.")

    d = state.Labels[match[0][3]][2]

    return (bits[:14] + format(d, "0>9b") + bits[23:])

# Instruction map:
# Key : opcode
# Value : tuple
#    Pattern:
#        0/1: initial bit value
#        d/s: d-field/s-field value
#        space: ignored
#        any other character: replaced with 0 if not set by any other means
#    Can override Z
#    Can override C
#    Can override R
#    Can override I
#    Can override condition
#    (optional) func that does some extra processing to bits

instructions = {}
instructions["ABS"]     = ("101010 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ABSNEG"]  = ("101011 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ADD"]     = ("100000 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ADDABS"]  = ("100010 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ADDS"]    = ("110100 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ADDSX"]   = ("110110 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ADDX"]    = ("110010 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["AND"]     = ("011000 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ANDN"]    = ("011001 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["CALL"]    = ("010111 0011 1111 ????????? sssssssss", True,    False,  True,   True,   True,   _fix_call)
instructions["CLKSET"]  = ("000011 0001 1111 ddddddddd ------000", False,   False,  False,  False,  True)
instructions["CMP"]     = ("100001 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["CMPS"]    = ("110000 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["CMPSUB"]  = ("111000 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["CMPSX"]   = ("110001 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["CMPX"]    = ("110011 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["COGID"]   = ("000011 0011 1111 ddddddddd ------001", True,    True,   True,   False,  True)
instructions["COGINIT"] = ("000011 0001 1111 ddddddddd ------010", True,    True,   True,   False,  True)
instructions["COGSTOP"] = ("000011 0001 1111 ddddddddd ------011", True,    True,   True,   False,  True)
instructions["DJNZ"]    = ("111001 001i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["HUBOP"]   = ("000011 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["JMP"]     = ("010111 000i 1111 --------- sssssssss", True,    True,   False,  True,   True)
instructions["JMPRET"]  = ("010111 001i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["LOCKCLR"] = ("000011 0001 1111 ddddddddd ------111", True,    True,   True,   False,  True)
instructions["LOCKNEW"] = ("000011 0011 1111 ddddddddd ------100", True,    True,   False,  False,  True)
instructions["LOCKRET"] = ("000011 0001 1111 ddddddddd ------101", True,    True,   True,   False,  True)
instructions["LOCKSET"] = ("000011 0001 1111 ddddddddd ------110", True,    True,   True,   False,  True)
instructions["MAX"]     = ("010011 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MAXS"]    = ("010001 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MIN"]     = ("010010 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MINS"]    = ("010000 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MOV"]     = ("101000 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MOVD"]    = ("010101 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MOVI"]    = ("010110 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MOVS"]    = ("010100 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MUXC"]    = ("011100 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MUXNC"]   = ("011101 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MUXNZ"]   = ("011111 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["MUXZ"]    = ("011110 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["NEG"]     = ("101001 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["NEGC"]    = ("101100 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["NEGNC"]   = ("101101 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["NEGNZ"]   = ("101111 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["NEGZ"]    = ("101110 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["NOP"]     = ("------ ---- 0000 --------- ---------", False,   False,  False,  False,  False)
instructions["OR"]      = ("011010 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["RCL"]     = ("001101 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["RCR"]     = ("001100 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["RDBYTE"]  = ("000000 001i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["RDLONG"]  = ("000010 001i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["RDWORD"]  = ("000001 001i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["RET"]     = ("010111 0001 1111 --------- ---------", True,    True,   True,   True,   True)
instructions["REV"]     = ("001111 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ROL"]     = ("001001 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["ROR"]     = ("001000 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SAR"]     = ("001110 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SHL"]     = ("001011 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SHR"]     = ("001010 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUB"]     = ("100001 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUBABS"]  = ("100011 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUBS"]    = ("110101 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUBSX"]   = ("110111 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUBX"]    = ("110011 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUMC"]    = ("100100 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUMNC"]   = ("100101 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUMNZ"]   = ("100111 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["SUMZ"]    = ("100110 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["TEST"]    = ("011000 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["TESTN"]   = ("011001 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["TJNZ"]    = ("111010 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["TJZ"]     = ("111011 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["WAITCNT"] = ("111110 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["WAITPEQ"] = ("111100 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["WAITPNE"] = ("111101 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["WAITVID"] = ("111111 000i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)
instructions["WRBYTE"]  = ("000000 000i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["WRLONG"]  = ("000010 000i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["WRWORD"]  = ("000001 000i 1111 ddddddddd sssssssss", True,    True,   False,  True,   True)
instructions["XOR"]     = ("011011 001i 1111 ddddddddd sssssssss", True,    True,   True,   True,   True)

for key, value in instructions.items():
    instructions[key] = (value[0].replace(" ", ""),) + value[1:]
    
    if len(instructions[key][0]) != 32:
        raise ValueError("The mask for {} does not contain 32 characters.".format(key))


reserved_words = directives                     \
                 + effects                      \
                 + datatypes                    \
                 + tuple(instructions.keys())   \
                 + tuple(conditions.keys())     \
                 + tuple(constants.keys())      \
                 + tuple(registers.keys())
