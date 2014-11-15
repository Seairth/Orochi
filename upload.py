#!/usr/bin/env python

# Orochi is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version. The
# software is distributed WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# the software.  If not, see <http://www.gnu.org/licenses/>.

# The following code is based on the "Parallax Propeller code uploader", written
# by Remy Blank.  The original code was release under GNU General Pulic License,
# version 2.  A copy of the original code may be found at
# http://forums.parallax.com/showthread.php/157773-Stand-alone-Programmer?p=1298179

import os
import time
import serial

# Processor constants
lfsrRequestLen = 250
lfsrReplyLen = 250
lfsrSeed = ord("P")

cmdShutdown = 0
cmdLoadRamRun = 1
cmdLoadEeprom = 2
cmdLoadEepromRun = 3

# Platform defaults
defSerial = {
    "posix": "/dev/ttyUSB0",
    "nt": "COM1",
}

def _lfsr(seed):
    """Generate bits from 8-bit LFSR with taps at 0xB2."""
    while True:
        yield seed & 0x01
        seed = ((seed << 1) & 0xfe) | (((seed >> 7) ^ (seed >> 5) ^ (seed >> 4) ^ (seed >> 1)) & 1)

def encode_long(value):
    """Encode a 32-bit long as short/long pulses."""
    result = bytearray()
    for i in range(10):
        result.append(0x92 | (value & 0x01) | ((value & 2) << 2) | ((value & 4) << 4))
        value >>= 3
    result.append(0xf2 | (value & 0x01) | ((value & 2) << 2))
    return result


def do_nothing(msg):
    """Default progress callback."""
    pass
    

class LoaderError(Exception): pass


class Loader(object):
    """Propeller code uploader."""
    eepromSize = 32768
    
    def __init__(self, port):
        self.serial = serial.Serial(baudrate=115200, timeout=0)
        self.serial.port = port
        
    # High-level functions
    def get_version(self, progress=do_nothing):
        """Connect to the Propeller and return its version."""
        self._open()
        try:
            version = self._connect()
            self._write_long(cmdShutdown)
            time.sleep(0.010)
            self._reset()
            return version
        finally:
            self._close()
        
    def upload(self, code=None, path=None, eeprom=False, run=True, progress=do_nothing):
        """Connect to the Propeller and upload code to RAM or EEPROM."""
        
        if path is not None:
            progress("Uploading {}".format(path))
            with open(path, "rb") as f:
                code = f.read()

        if len(code) % 4 != 0:
            raise LoaderError("Invalid code size: must be a multiple of 4")

        if eeprom and len(code) < self.eepromSize:
            code = self._bin_to_eeprom(code)

        checksum = sum(code)
        
        if not eeprom:
            checksum += 2 * (0xff + 0xff + 0xf9 + 0xff)

        checksum &= 0xff

        if checksum != 0:
            raise LoaderError("Code checksum error: 0x{:0>2x}".format(checksum))

        self._open()
        try:
            version = self._connect()
            progress("Connected (version={})".format(version))
            self._send_code(code, eeprom, run, progress)
        finally:
            self._close()
    
    # Low-level functions
    def _open(self):
        self.serial.open()
    
    def _close(self):
        self.serial.close()
        
    def _reset(self):
        self.serial.flushOutput()
        self.serial.setDTR(1)
        time.sleep(0.025)
        self.serial.setDTR(0)
        time.sleep(0.090)
        self.serial.flushInput()
        
    def _calibrate(self):
        self._write_byte(0xf9)
        
    def _connect(self):
        self._reset()
        self._calibrate()
        
        seq = []
        
        for (i, value) in zip(range(lfsrRequestLen + lfsrReplyLen), _lfsr(lfsrSeed)):
            seq.append(value)
        
        self.serial.write(bytes((each | 0xfe) for each in seq[0:lfsrRequestLen]))
        self.serial.write(bytes((0xf9,) * (lfsrReplyLen + 8)))
        
        for i in range(lfsrRequestLen, lfsrRequestLen + lfsrReplyLen):
            if self._read_bit(False, 0.100) != seq[i]:
                raise LoaderError("No hardware found")
        
        version = 0
        for i in range(8):
            version = ((version >> 1) & 0x7f) | ((self._read_bit(False, 0.050) << 7))
        
        return version

    def _bin_to_eeprom(self, code):
        if len(code) > self.eepromSize - 8:
            raise LoaderError("Code too long for EEPROM (max {} bytes)".format(self.eepromSize - 8))
        
        dbase = code[0x0a] + (code[0x0b] << 8)
        
        if dbase > self.eepromSize:
            raise LoaderError("Invalid binary format")
        
        eeprom = bytearray(code)
        eeprom += bytearray([0x00] * (dbase - 8 - len(code)))
        eeprom += bytearray([0xff, 0xff, 0xf9, 0xff] * 2)
        eeprom += bytearray([0x00] * int(self.eepromSize - len(code)))
        
        return eeprom
        
    def _send_code(self, code, eeprom=False, run=True, progress=do_nothing):
        command = [cmdShutdown, cmdLoadRamRun, cmdLoadEeprom, cmdLoadEepromRun][eeprom * 2 + run]
        
        self._write_long(command)
        
        if not eeprom and not run:
            return
        
        self._write_long(len(code) // 4)
        progress("Sending code ({} bytes)".format(len(code)))
        
        i = 0
        while i < len(code): 
            self._write_long(code[i] | (code[i + 1] << 8) | (code[i + 2] << 16) | (code[i + 3] << 24))
            i += 4
        
        if self._read_bit(True, 8) == 1:
            raise LoaderError("RAM checksum error")
        
        if eeprom:
            progress("Programming EEPROM")
            if self._read_bit(True, 5) == 1:
                raise LoaderError("EEPROM programming error")
        
            progress("Verifying EEPROM")
            if self._read_bit(True, 2.5) == 1:
                raise LoaderError("EEPROM verification error")

    # Lowest-level functions
    def _write_byte(self, value):
        self.serial.write(bytes((value,)))
        
    def _write_long(self, value):
        self.serial.write(encode_long(value))
        
    def _read_bit(self, echo, timeout):
        start = time.time()
        while time.time() - start < timeout:
            if echo:
                self._write_byte(0xf9)
                time.sleep(0.025)
            c = self.serial.read(1)
            if c:
                if c[0] in (0xfe, 0xff):
                    return c[0] & 0x01
                else:
                    raise LoaderError("Bad reply")
        raise LoaderError("Timeout error")

def get_version(serial):
    """Get the version of the connected Propeller chip."""

    loader = Loader(serial)
    print(loader.get_version())

def upload(serial, path, eeprom=False, run=True, progress=do_nothing):
    """Upload file on given serial port."""

    loader = Loader(serial)
    loader.upload(path=path, eeprom=eeprom, run=run, progress=progress)
    progress("Done")

def printStatus(msg):
    """Print status messages."""
    print(msg)
    
def _action_get_version(args):
    get_version(args.serial)

def _action_upload(args):
    path = args.filename

    if path.endswith(".eeprom"):
        args.destination = "EEPROM"
    else:
        args.destination = args.destination.upper()
    
    try:
        upload(args.serial, path, (args.destination == "EEPROM"), args.run, printStatus)
    except (SystemExit, KeyboardInterrupt):
        return 3
    except Exception as e:
        sys.stderr.write(str(e) + "\n")
        return 1

if __name__ == "__main__":
    import sys
    import argparse

    parser = argparse.ArgumentParser()

    parser.add_argument("-v",   "--version", action="version", version="%(prog)s 0.1",
                        help="Show the program version and exit.")

    subparsers = parser.add_subparsers()

    parser_v = subparsers.add_parser("version")
    parser_v.set_defaults(action=_action_get_version)
    parser_v.add_argument("-s", "--serial", dest="serial", type=str, metavar="DEVICE", default=defSerial.get(os.name, "none"),
                          help="Select the serial port device. The default is %(default)s.")

    parser_u = subparsers.add_parser("upload")
    parser_u.set_defaults(action=_action_upload)
    parser_u.add_argument("filename", type=str,
                          help="Binary file to be uploaded.")
    parser_u.add_argument("-d", "--destination", type=str, default="RAM", choices=["RAM", "EEPROM"],
                          help="Upload to RAM or to EEPROM.  The default is %(default)s.")
    parser_u.add_argument("-n", "--no-run", action="store_false", dest="run", default=True,
                          help="Don't run the code after upload.")
    parser_u.add_argument("-s", "--serial", dest="serial", type=str, metavar="DEVICE", default=defSerial.get(os.name, "none"),
                          help="Select the serial port device. The default is %(default)s.")

    args = parser.parse_args()

    if hasattr(args, "action"):
        exit(args.action(args))

    parser.print_usage()
