
# Orichi is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation,
# either version 3 of the License, or (at your option) any later version. The
# software is distributed WITHOUT ANY WARRANTY; without even the implied warranty
# of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
# 
# You should have received a copy of the GNU General Public License along with
# the software.  If not, see <http://www.gnu.org/licenses/>.

import re

class AddressOutOfRangeError(Exception): pass

class AssemblerError(Exception):
    def __init__(self, line_number : int, message : str):
        Exception.__init__(self)
        self.LineNumber = line_number
        self.Message = message

class State:
    label_re = re.compile(":?[_A-Z][_A-Z0-9]*", re.IGNORECASE);

    def __init__(self):
        self.LineNumber = 0
        self.CogAddress = 0
        self.HubAddress = 1
        self.CurrentLabel = ""
        self.Labels = []
        self.Instructions = []

        self.Errors = []

    def ORG(self, address : int = 0):
        if address < 0 or address > 0x1FF:
            raise AddressOutOfRangeError()

        self.CogAddress = address
    
    def FIT(self, address : int = 0x1F0):
        if address < 0 or address > 0x1F0:
            raise AddressOutOfRangeError()

        return (self.CogAddress < address)

    def RES(self, count : int = 1):
        if count < 1 or (self.CogAddress + count) > 0x1FF:
            raise AssemblerError(self.LineNumber, "The value for RES is out of range.")

        self.CogAddress += count

    def SetLineNumber(self, line_number : int):
        self.LineNumber = line_number

        matches = [l for l in self.Labels if l[1] <= line_number and ":" not in l[0]]

        if matches:
            self.CurrentLabel = matches[-1][0]
        else:
            self.CurrentLabel = ""

    def AddLabel(self, label : str) -> bool:
        '''Validates a label and adds it to the label collection
            Returns true if added, returns false otherwise'''

        if not State.label_re.match(label):
            return False

        if label[0] == ":":
            label = self.CurrentLabel + label
        else:
            self.CurrentLabel = label

            if label.endswith("_RET"):
                for l in reversed(self.Labels):
                    if label == (l[0] + "_RET"):
                        l.append(len(self.Labels))
                        break

        if label in self.Labels:
            return False

        self.Labels.append([label, self.LineNumber, -1, -1])

        return True

    def FixLabelAddresses(self):
        for label in reversed(self.Labels):
            if label[2] != -1:
                break

            label[2] = self.CogAddress
            label[3] = self.HubAddress

    def GetLabelAddress(self, name : str, hub_address : bool = False) -> int:
        if name[0] == ":":
            name = self.CurrentLabel + name

        match = [l for l in self.Labels if l[0] == name]

        return None if not match else match[0][3 if hub_address else 2]

    def AddError(self, error : AssemblerError):
        self.Errors.append(error)