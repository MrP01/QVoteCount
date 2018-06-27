import datetime
import struct

Int8Packer = struct.Struct("!b")
Int16Packer = struct.Struct("!h")
Int32Packer = struct.Struct("!i")
Int64Packer = struct.Struct("!l")
UInt8Packer = struct.Struct("!B")
UInt16Packer = struct.Struct("!H")
UInt32Packer = struct.Struct("!I")
UInt64Packer = struct.Struct("!L")
BoolPacker = struct.Struct("!?")
FloatPacker = struct.Struct("!f")
DoublePacker = struct.Struct("!d")
DateTimePacker = struct.Struct("!HBBBBB")


def _write(device, packer, *values):
    device.extend(packer.pack(*values))


def _read(device, packer):
    values = packer.unpack_from(device)
    del device[0:packer.size]
    return values


def writeInt8(device, value):
    _write(device, Int8Packer, value)


def readInt8(device):
    return _read(device, Int8Packer)[0]


def writeInt16(device, value):
    _write(device, Int16Packer, value)


def readInt16(device):
    return _read(device, Int16Packer)[0]


def writeInt32(device, value):
    _write(device, Int32Packer, value)


def readInt32(device):
    return _read(device, Int32Packer)[0]


def writeInt64(device, value):
    _write(device, Int64Packer, value)


def readInt64(device):
    return _read(device, Int64Packer)[0]


def writeUInt8(device, value):
    _write(device, UInt8Packer, value)


def readUInt8(device):
    return _read(device, UInt8Packer)[0]


def writeUInt16(device, value):
    _write(device, UInt16Packer, value)


def readUInt16(device):
    return _read(device, UInt16Packer)[0]


def writeUInt32(device, value):
    _write(device, UInt32Packer, value)


def readUInt32(device):
    return _read(device, UInt32Packer)[0]


def writeUInt64(device, value):
    _write(device, UInt64Packer, value)


def readUInt64(device):
    return _read(device, UInt64Packer)[0]


def writeBool(device, value):
    _write(device, BoolPacker, value)


def readBool(device):
    return _read(device, BoolPacker)[0]


def writeFloat(device, value):
    _write(device, FloatPacker, value)


def readFloat(device):
    return _read(device, FloatPacker)[0]


def writeDouble(device, value):
    _write(device, DoublePacker, value)


def readDouble(device):
    return _read(device, DoublePacker)[0]


def writeBlob(device, value):
    writeUInt16(device, len(value))
    device.extend(value)


def readBlob(device):
    count = readUInt16(device)
    value = device[0:count]
    del device[0:count]
    return value


def writeString(device, value, encoding="utf-8"):
    writeBlob(device, value.encode(encoding))


def readString(device, encoding="utf-8"):
    return readBlob(device).decode(encoding)


def writeDateTime(device, value):
    _write(device, DateTimePacker, value.year, value.month,
           value.day, value.hour, value.minute, value.second)


def readDateTime(device):
    return datetime.datetime(*_read(device, DateTimePacker))


class DataStream(object):
    def __init__(self, device=None, encoding="utf-8"):
        if device is None:
            self.device = bytearray()
        else:
            self.device = device
        self.encoding = encoding

    def writeInt8(self, value):
        writeInt8(self.device, value)

    def readInt8(self):
        return readInt8(self.device)

    def writeInt16(self, value):
        writeInt16(self.device, value)

    def readInt16(self):
        return readInt16(self.device)

    def writeInt32(self, value):
        writeInt32(self.device, value)

    def readInt32(self):
        return readInt32(self.device)

    def writeInt64(self, value):
        writeInt64(self.device, value)

    def readInt64(self):
        return readInt64(self.device)

    def writeUInt8(self, value):
        writeUInt8(self.device, value)

    def readUInt8(self):
        return readUInt8(self.device)

    def writeUInt16(self, value):
        writeUInt16(self.device, value)

    def readUInt16(self):
        return readUInt16(self.device)

    def writeUInt32(self, value):
        writeUInt32(self.device, value)

    def readUInt32(self):
        return readUInt32(self.device)

    def writeUInt64(self, value):
        writeUInt64(self.device, value)

    def readUInt64(self):
        return readUInt64(self.device)

    def writeBool(self, value):
        writeBool(self.device, value)

    def readBool(self):
        return readBool(self.device)

    def writeFloat(self, value):
        writeFloat(self.device, value)

    def readFloat(self):
        return readFloat(self.device)

    def writeDouble(self, value):
        writeDouble(self.device, value)

    def readDouble(self):
        return readDouble(self.device)

    def writeString(self, value):
        writeString(self.device, value, self.encoding)

    def readString(self):
        return readString(self.device, self.encoding)

    def writeDateTime(self, value):
        writeDateTime(self.device, value)

    def readDateTime(self):
        return readDateTime(self.device)

    def writeBlob(self, value):
        writeBlob(self.device, value)

    def readBlob(self):
        return readBlob(self.device)

    def device(self):
        return self._device

    def setDevice(self, device):
        if isinstance(device, bytes):
            device = bytearray(device)
        self._device = device

    device = property(device, setDevice)

    def encoding(self):
        return self._encoding

    def setEncoding(self, encoding):
        self._encoding = encoding

    encoding = property(encoding, setEncoding)
