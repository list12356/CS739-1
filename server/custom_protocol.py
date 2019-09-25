class Message(object):
    PUT = 1
    GET = 0
    def __init__(self):
        self.Op = 0
        self.time = 0
        self.key = ""
        self.value = ""
        self.oldValue = ""
        self.returnValue = 0
        self.hasValue = 0
        self.hasOldValue = 0

    
    def print(self):
        print(self.__dict__)


class CustomProtocol(object):
    def __init__(self):
        pass

    def decode(self, string):
        msg = Message()
        msg.Op = int.from_bytes(string[0:4], byteorder='little')
        msg.time = int.from_bytes(string[4:8], byteorder='little')
        msg.returnValue = int.from_bytes(string[8:12], byteorder='little')
        msg.hasOldValue = string[12]
        msg.hasValue = string[13]
        msg.key = string[128:256].decode("ascii").rstrip('\x00')
        msg.value = string[256:2304].decode("ascii").rstrip('\x00')
        msg.oldValue = string[2304:4352].decode("ascii").rstrip('\x00')
        return msg

    def encode(self, msg):
        # msg.Op
        string = (0).to_bytes(4, byteorder='little')
        string += (msg.time).to_bytes(4, byteorder='little')
        string += (msg.returnValue).to_bytes(4, byteorder='little')
        string += (msg.hasOldValue).to_bytes(1, byteorder='little')
        string += (msg.hasValue).to_bytes(1, byteorder='little')
        # padding the space
        string = string.ljust(128, b'\0')
        string += msg.key.encode('ascii').ljust(128, b'\0')
        string += msg.value.encode('ascii').ljust(2048, b'\0')
        string += msg.oldValue.encode('ascii').ljust(2048, b'\0')
        return string