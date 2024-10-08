from PySide6.QtCore import QRect

from base.dataStream import DataStream


class QtDataStream(DataStream):
    # _QDataStream=QDataStream()
    def writeQRect(self, rect):
        self.writeInt16(rect.x())
        self.writeInt16(rect.y())
        self.writeInt16(rect.width())
        self.writeInt16(rect.height())

    def readQRect(self):
        return QRect(self.readInt16(), self.readInt16(), self.readInt16(), self.readInt16())


# def _writeQtObj(self, fun, obj):
# 	fun(obj)
# 	MyDataStream._QDataStream.device().

# def setDevice(self, device):
# 	print("setDevice")
# 	if isinstance(device, QByteArray):
# 		DataStream.setDevice(self, _QByteArrayStreamer(bytearray(), device))
# 	DataStream.setDevice(self, device)
# 	print(self.device)
# def device(self):
# 	return QByteArray(bytes(DataStream.device.fget(self)))
# device=property(device, setDevice)

# class _QByteArrayStreamer(object):    #limited support
# 	def __init__(self, target=None, src=None):
# 		self.target=target
# 		if self.target is None:
# 			self.target=QByteArray()
# 		if src is not None:
# 			self.extend(src)
#
# 	def extend(self, data):
# 		self.target.append(data)
#
# 	def __bytes__(self):
# 		return self.target.data()
# 	def __getitem__(self, item):
# 		return self.target[item]
# 	def __setitem__(self, key, value):
# 		self.target[key]=value
# 	def __delitem__(self, key):
# 		del self.target[key]
