# Orochi

Orochi (Yamata no Orochi) : A mythical Japanese serpent with eight heads
and eight tails.  See: <http://en.wikipedia.org/wiki/Yamata_no_Orochi>

## Overview
Orochi is a set of Python-based command-line tools for the Parallax Propeller.
Though they can be used with the Propeller 1, their primary purpose is to allow
_easy_ modification for experimentation with the Propeller 1 Verilog.

Currently, there are two tools:

> pasm : PASM assember  
> upload : Binary/EEPROM Uploader

## Dependencies

* Python (3.4 or newer)
* PyParsing (2.0 or newer)
* PySerial (2.7 or newer)

## Files

    pasm.py             PASM assembler  
    upload.py               Binary/EEPROM uploader

    assembler           (package used by pasm.py)
        expression.py   PyParsing code for constant expression evaluation
        lang.py         Tables for mapping code to binary patterns
        state.py        Shared state structure

## License

Orichi is free software: you can redistribute it and/or modify it under the terms
of the GNU General Public License as published by the Free Software Foundation,
either version 3 of the License, or (at your option) any later version. The
software is distributed WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
Public License for more details.

## Caveats

This toolset does not support standard SPIN files.  To convert a SPIN file into a compatible
format (usually with the .pasm extension), remove all SPIN code (including "DAT"), except the
assembler portion.  In other words, the first line of code will be ORG, or an assembly
instruction.  With the current version, code always starts execution with the first instruction.

Additionally, this version of Propeller Assembler currently has one non-standard syntax element.
The ampersand (@), when encountered in a constant expression, evaluates to the effective Hub address
of the referenced label.  In other words, it is not affected by the ORG directive and starts with an
initial value that accounts for the small SPIN bootstrap that take up the first few longs of Hub
memory.

## To-do:

* Add command-line option to start execution at an address other than zero.
* Add command-line option for setting the clock configuration (currently hardwired at 80MHz)
