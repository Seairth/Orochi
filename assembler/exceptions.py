class ErrorBase(Exception) : pass

class AddressOutOfRangeError(ErrorBase): pass

class AssemblerError(ErrorBase):
    def __init__(self, line_number : int, message : str):
        Exception.__init__(self)
        self.LineNumber = line_number
        self.Message = message
