#!/usr/bin/env python

# Orichi is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version. The
# software is distributed WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# the software.  If not, see <http://www.gnu.org/licenses/>.

import argparse
import os
import sys
import assembler
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-v", "--version", action="version", version="%(prog)s 0.1")
    parser.add_argument("-s", "--syntax", type=int, default=1, choices=(1,),
                        help="Syntax version of PASM code.")
    parser.add_argument("-f", "--format", type=str, default="binary", choices=["binary", "eeprom", "raw"],
                        help="Save as a binary with the SPIN bootstrap, EEPROM image with SPIN bootstrap, or without any bootstrap. Default: %(default)s.")
    parser.add_argument("-x", "--hex", action="store_true", default=False,
                        help="Save output as a hex textfile.")

    parser.add_argument("-b", "--hub_offset", type=int, default=1,
                        help="The initial value for the @ symbol.")

    parser.add_argument("-o", "--output", type=str, default="",
                        help="Filename to save to (default is input filename with appropriate extension)")
    parser.add_argument("filename", type=str, default="",
                        help="Filename to be compiled.")
    
    args = parser.parse_args()

    if args.filename == "":
        parser.print_help()
        sys.exit(-1)

    try:
        f = open(args.filename)
    except OSError:
        print("Failed to open file \"{0}\"!".format(args.filename))

    data = assembler.assemble(f, args.format, args.hub_offset, syntax_version = args.syntax)

    # Now, write it out...
    outfile = os.path.splitext(args.filename)[0]

    if args.output:
        outfile = args.output
    elif args.format == "binary":
        outfile += ".binary"
    elif args.format == "eeprom":
        outfile += ".eeprom"
    else:
        outfile += ".raw"

    with open(outfile, "w+b") as f:
        f.write(data)

    if args.hex:
        outfile += ".hex"
    
        with open(outfile, "w+") as f:
            count = 0

            for b in data:
                if count % 4 == 0:
                    if count % 16 == 0:
                        f.write("\n")
                    else:
                        f.write(" ")

                f.write(format(b, "0>2x").upper())
            
                count += 1
