# Orichi is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version. The
# software is distributed WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# the software.  If not, see <http://www.gnu.org/licenses/>.

import sys
import math
from pyparsing import Literal, Word, Combine, Optional, Forward, ZeroOrMore
from pyparsing import nums, alphanums, alphas, hexnums, quotedString
from .state import State
from .exceptions import AssemblerError
from . import lang

__all__ = ["ConstantExpression"]

class ConstantExpression(object):
    """performs expression parsing and evaluation for PASM constant expressions"""

    def __init__(self, state : State ):
        self._state = state
        self._stack = []

        self._bnf = self._BNF()

    def _resolve_label(self, label : str) -> int:
        hub_address = (label[0] == "@")

        if hub_address:
            label = label[1:]

        value = self._state.GetLabelAddress(label, hub_address)

        if value is None:
            raise AssemblerError(self._state.LineNumber, "Could not resolve label: {}".format(label))

        return value

    def _resolve_constant(self, contant : str) -> int:

        if constant not in lang.constants:
            raise AssemblerError(self._state.LineNumber, "Could not resolve constant: {}".format(constant))

        return lang.constants[constant]

    def _resolve_register(self, register : str) -> int:
        if register not in lang.registers:
            raise AssemblerError(self._state.LineNumber, "Could not resolve register: {}".format(register))

        return lang.registers[register]

    def _binary2int(self, binary):
        value = int(binary[1:].replace("_",""), 2)

        if value > 0x7FFFFFFF:
            value -= 0x100000000

        return value

    def _quaternary2int(self, quaternary):
        value = int(quaternary[2:].replace("_",""), 4)

        if value > 0x7FFFFFFF:
            value -= 0x100000000

        return value

    def _hex2int(self, hex):
        value = int(hex[1:].replace("_",""), 16)

        if value > 0x7FFFFFFF:
            value -= 0x100000000

        return value

    def _mark_name_token(self, tokens):
        if tokens[0] in lang.registers:
            return ["r" + tokens[0]]
        
        if tokens[0] in lang.constants:
            return ["c" + tokens[0]]

        return ["l" + tokens[0]]

    def _mark_unary(self, tokens):
        return ["u" + tokens[0]]

    def _push(self, tokens):
        # print("Pushing Token => {}".format(tokens[0]))

        self._stack.append(tokens[0])

    def _BNF(self):
        base16 = Literal("$")
        hex = Combine(base16 + Word(hexnums + "_"))

        base4 = Literal("%%")
        quaternary = Combine(base4 + Word("0123_"))

        base2 = Literal("%")
        binary = Combine(base2 + Word("01_"))

        plusminus = Literal("+") | Literal("-")
        integer = Combine(Optional(plusminus) + Word(nums+"_"))

        name_token = Combine(Optional(Literal(":") | Literal("@")) + Word("_" + alphas, "_" + alphanums))
        name_token.setParseAction(self._mark_name_token)

        lparens = Literal("(").suppress()
        rparens = Literal(")").suppress()

        # op0 = Literal("@")
        op1 = (Literal("^^") | Literal("||") | Literal("|<") | Literal(">|") | Literal("!")).setParseAction(self._mark_unary)
        op2 = Literal("->") | Literal("<-") | Literal(">>") | Literal("<<") | Literal("~>") | Literal("><")
        op3 = Literal("&")
        op4 = Literal("|") | Literal("^")
        op5 = Literal("**") | Literal("*") | Literal("//") | Literal("/")
        op6 = Literal("+") | Literal("-")
        op7 = Literal("#>") | Literal("<#")
        op8 = Literal("<") | Literal(">") | Literal("<>") | Literal("==") | Literal("=<") | Literal("=>")
        op9 = Literal("NOT").setParseAction(self._mark_unary)
        op10 = Literal("AND")
        op11 = Literal("OR")
        op12 = Literal(",")

        expr = Forward()

        atom = name_token | hex | quaternary | binary | integer | quotedString
        atom.setParseAction(self._push)
        atom = atom | (lparens + expr.suppress() + rparens)
 
        # term0  = atom   + ZeroOrMore((op0 + atom)   .setParseAction(self._push))
        # term1  = term0  + ZeroOrMore((op1 + term0)  .setParseAction(self._push))
        term1  = atom   + ZeroOrMore((op1 + atom)   .setParseAction(self._push))
        term2  = term1  + ZeroOrMore((op2 + term1)  .setParseAction(self._push))
        term3  = term2  + ZeroOrMore((op3 + term2)  .setParseAction(self._push))
        term4  = term3  + ZeroOrMore((op4 + term3)  .setParseAction(self._push))
        term5  = term4  + ZeroOrMore((op5 + term4)  .setParseAction(self._push))
        term6  = term5  + ZeroOrMore((op6 + term5)  .setParseAction(self._push))
        term7  = term6  + ZeroOrMore((op7 + term6)  .setParseAction(self._push))
        term8  = term7  + ZeroOrMore((op8 + term7)  .setParseAction(self._push))
        term9  = term8  + ZeroOrMore((op9 + term8)  .setParseAction(self._push))
        term10 = term9  + ZeroOrMore((op10 + term9) .setParseAction(self._push))
        term11 = term10 + ZeroOrMore((op11 + term10).setParseAction(self._push))
        expr  << term11 + ZeroOrMore((op12 + term11).setParseAction(self._push))

        return expr

    def Evaluate(self, expression : str) -> int:
        self._bnf.parseString(expression)

        return self._evaluate()

    def _bitwise_encode(value : int) -> int:
        if value == 0:
            return 0

        count = 1

        while value != 0:
            value >> 1
            count += 1

        return count

    _unary_ops = {
        "+"  : ( lambda a : a),
        "-"  : ( lambda a : -a),
        "^^" : ( lambda a : int(math.sqrt(a))),
        "||" : ( lambda a : int(math.fabs(a))),
        "|<" : ( lambda a : 1 << a),
        ">|" : _bitwise_encode,
        "!"  : ( lambda a : ~a),
        "NOT" : ( lambda a : -1 if a == 0 else 0)
        }    

    def _bitwise_rotate_left(value : int, count : int) -> int:
        if count == 0:
            return value

        _v = format(value, "0>32b")
        _v = _v[count:] + _v[:count]
        return int(_v, 2)

    def _bitwise_rotate_right(value : int, count : int) -> int:
        if count == 0:
            return value

        _v = format(value, "0>32b")
        _v = _v[-count:] + _v[:-count]
        return int(_v, 2)

    def _arithmetic_shift_right(value : int, count : int) -> int:
        if count == 0:
            return value

        _v = format(value, "0>32b")
        sign = _v[0]
        _v = (sign * count) + _v[:-count]
        return int(_v, 2)

    def _bitwise_reverse_bits(value : int, count : int) -> int:
        _v = format(value, "0>32b")
        _v = ("0" * (32 - count)) + reversed(_v)[:count]
        return int(_v, 2)

    _binary_ops = {
        "+"  : ( lambda a, b: a+b),
        "-"  : ( lambda a, b: a-b),
        "*"  : ( lambda a, b: (a*b) & 0xFFFFFFFF),
        "**" : ( lambda a, b: (a*b) >> 32),
        "/"  : ( lambda a, b: int(a/b)),
        "//" : ( lambda a, b: a%b),
        "<<" : ( lambda a, b: a<<b),
        ">>" : ( lambda a, b: a>>b),
        "->" : _bitwise_rotate_right,
        "<-" : _bitwise_rotate_left,
        "~>" : _arithmetic_shift_right,
        "><" : _bitwise_reverse_bits,
        "&"  : ( lambda a, b: a&b),
        "|"  : ( lambda a, b: a|b),
        "^"  : ( lambda a, b: a^b),
        "#>" : ( lambda a, b: a if a > b else b),
        "<#" : ( lambda a, b: a if a < b else b),
        "<"  : ( lambda a, b: -1 if a<b  else 0),
        ">"  : ( lambda a, b: -1 if a>b  else 0),
        "<>" : ( lambda a, b: -1 if a!=b else 0),
        "==" : ( lambda a, b: -1 if a==b else 0),
        "=<" : ( lambda a, b: -1 if a<=b else 0),
        ">=" : ( lambda a, b: -1 if a>=b else 0),
        "AND" : ( lambda a, b: -1 if bool(a) and bool(b) else 0),
        "OR"  : ( lambda a, b: -1 if bool(a) or bool(b) else 0),
        }

    def _evaluate(self):
        op = self._stack.pop()
        
        # print("Popped => {}".format(op))

        if op[0] == "c":
            return self._resolve_constant(op[1:])

        if op[0] == "l":
            return self._resolve_label(op[1:])

        if op[0] == "r":
            return self._resolve_register(op[1:])

        # if op[0] == "@":
        #     op1 = self._stack.pop()
        # 
        #     if op1[0] != "r":
        #         raise AssemblerError(self._state.LineNumber, "Symbol Address operator is not followed by a label.")
        # 
        #     return self._resolve_label(op1[1:], True)

        if op[0] == "$":
            return self._hex2int(op)

        if op[:2] == "%%":
            return self._quaternary2int(op)

        if op[0] == "%":
            return self._binary2int(op)

        if op[0] in "\"'":
            return [ord(c) for c in op[1:-1]]

        if op.replace("_","")[0].isdigit():
            return int(op.replace("_",""))

        if op[0] == "u":
            op1 = self._evaluate()
            value = int(ConstantExpression._unary_ops[op[1:]](op1))
            return value

        op2 = self._evaluate()
        op1 = self._evaluate()

        if op == ",":
            if isinstance(op1, list):
                op1.append(op2)
                return op1

            return [op1, op2]

        if op in ConstantExpression._binary_ops:
            value = int(ConstantExpression._binary_ops[op](op1, op2))
            return value

        raise NotImplementedError("Token '{}' support is not implemented.".format(op))