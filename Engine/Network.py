import netifaces

from PySide6.QtCore import (QObject, QByteArray, QDataStream, QIODevice, QThread, Signal, QEventLoop, QTimer)
from PySide6.QtNetwork import (QAbstractSocket, QTcpServer, QTcpSocket)
from base.ItemStorage import ItemStorage, Item
from base.dataStream import DataStream

SIZEOF_UINT16 = 2


class NetworkError(Exception):
    NotConnected, RequestWrongState, IncompleteRead, Timeout = range(4)

    def __init__(self, type):
        Exception.__init__(self)
        self.type = type


class SocketAdapter(QObject):
    messageReceived = Signal(bytearray)

    def __init__(self, socket=None, parent=None):
        QObject.__init__(self, parent)
        self.socket = socket
        self.data = None
        self.nextBlockSize = 0

    def socket(self):
        return self._socket

    def setSocket(self, sock):
        self._socket = sock
        self._socket.readyRead.connect(self.receive)

    socket = property(socket, setSocket)

    def send(self, data):
        if self.socket.state() != QAbstractSocket.ConnectedState:
            raise NetworkError(NetworkError.NotConnected)
        _data = QByteArray()
        stream = QDataStream(_data, QIODevice.WriteOnly)
        stream.writeUInt16(len(data))
        _data.append(bytes(data))
        size = self.socket.write(_data)
        self.socket.waitForBytesWritten()
        return size

    def receive(self):
        available = self.socket.bytesAvailable()
        if not available:
            return
        if not self.isReceiving:
            stream = QDataStream(self.socket)
            self.data = bytearray()
            if available <= SIZEOF_UINT16:
                raise NetworkError(NetworkError.IncompleteRead)
            self.nextBlockSize = stream.readUInt16()
        self.data.extend(self.socket.read(self.nextBlockSize - len(self.data)).data())
        if len(self.data) == self.nextBlockSize:
            self.nextBlockSize = 0
            self.messageReceived.emit(self.data)

    @property
    def isReceiving(self):
        return self.nextBlockSize != 0


class Interface(object):
    class Error(Exception):
        pass  # Not Connected

    AF_INET, AF_INET6 = range(2)

    def __init__(self, name="", addresses=(), netmasks=()):
        self.name = name
        self.addresses = addresses
        self.netmasks = netmasks

    def address(self, family):
        return self.addresses[family]

    def netmask(self, family):
        return self.netmasks[family]

    @staticmethod
    def getInterface(name):
        if name not in netifaces.interfaces():
            raise ValueError("Interface is invalid")
        interface = Interface()
        interface.name = name
        addresses = netifaces.ifaddresses(name)
        if not netifaces.AF_INET in addresses.keys():
            raise Interface.Error()
        interface.addresses = [addresses[x][0]["addr"] for x in (netifaces.AF_INET, netifaces.AF_INET6)]
        interface.netmasks = [addresses[x][0]["netmask"] for x in (netifaces.AF_INET, netifaces.AF_INET6)]
        return interface

    @staticmethod
    def getInterfaces():
        interfaces = list()
        for iName in netifaces.interfaces():
            try:
                interfaces.append(Interface.getInterface(iName))
            except Interface.Error:
                pass
        return interfaces

    @staticmethod
    def getInterfaceNames():
        return [interface.name for interface in Interface.getInterfaces()]


# Client API

class RequestArguments(object):
    pass


class Request(QObject, Item):
    responseArrived = Signal(bytearray, RequestArguments)
    RequestNotSent, WaitingForResponse, Finished = list(range(3))

    def __init__(self, office, description=str(), data=None):
        QObject.__init__(self, office)
        Item.__init__(self)
        self.postOffice = office
        self.description = description
        self.data = data
        self.response = None
        self.args = RequestArguments()  # Not sent, used when response arrives
        self.state = Request.RequestNotSent
        if self.data is None:
            self.data = bytearray()

    def send(self):
        self.postOffice.issueRequest(self)
        self.state = Request.WaitingForResponse

    def waitForResponse(self, timeout=3000):
        if self.postOffice.socket.state() != QAbstractSocket.ConnectedState:
            raise NetworkError(NetworkError.NotConnected)
        if not (self.state in (Request.WaitingForResponse, Request.Finished)):
            raise NetworkError(NetworkError.RequestWrongState)
        loop = QEventLoop()
        QTimer.singleShot(timeout, loop.quit)
        self.postOffice.socket.error.connect(loop.quit)
        self.postOffice.socket.disconnected.connect(loop.quit)

        def responseArrived():
            loop.exit(1)

        self.responseArrived.connect(responseArrived)
        if not loop.exec_():
            raise NetworkError(NetworkError.Timeout)

    def receiveResponse(self, data):
        self.state = Request.Finished
        self.response = data
        self.responseArrived.emit(data, self.args)


class PostOffice(QObject):
    def __init__(self, socket=None, parent=None):
        QObject.__init__(self, parent)
        self.requests = ItemStorage()
        self.sockAdapter = SocketAdapter(socket, self)
        self.sockAdapter.messageReceived.connect(self.receiveResponse)

    def issueRequest(self, request):
        data = bytearray()
        stream = DataStream(data)
        request.id = self.requests.addItem(request)
        stream.writeUInt16(request.id)
        stream.writeString(request.description)
        stream.writeByteArray(request.data)
        return self.sockAdapter.send(data)

    def receiveResponse(self, data):
        stream = DataStream(data)
        if stream.readBool():
            request = self.requests.getItem(stream.readUInt16())
            request.receiveResponse(stream.readByteArray())
            self.requests.removeItem(request.id)
        else:
            self.handleServerNotification(stream.readString(), stream.readByteArray())

    def handleServerNotification(self, description, data):
        raise NotImplementedError()

    def socket(self):
        return self.sockAdapter.socket

    def setSocket(self, sock):
        self.sockAdapter.socket = sock

    socket = property(socket, setSocket)


# Server API

class Server(QTcpServer):
    def __init__(self, parent=None):
        QTcpServer.__init__(self, parent)
        self.clients = ItemStorage()

    def incomingConnection(self, socketId):
        clientThread = ClientThread(self, socketId)
        self.addClient(clientThread)
        clientThread.start()

    def connectionClosed(self, clientId):
        self.removeClient(clientId)

    def notifyAllClients(self, description, data):
        for client in self.clients:
            client.handler.notify(description, data)

    def addClient(self, clientThread):
        self.clients.addItem(clientThread)

    def removeClient(self, clientId):
        self.clients.getItem(clientId).deleteLater()
        self.clients.removeItem(clientId)


class ClientThread(QThread, Item):
    def __init__(self, server, socketId):
        QThread.__init__(self, server)
        Item.__init__(self)
        self.server = server
        self.handler = None
        self.socketId = socketId
        self.finished.connect(self._finished)

    def createHandler(self):
        socket = QTcpSocket()
        if not socket.setSocketDescriptor(self.socketId):
            raise NetworkError()
        socket.disconnected.connect(self.quit)
        return SocketHandler(socket)

    def prepare(self):  # Executed in Thread before handling
        pass

    def finish(self):  # Executed in Thread after disconnected
        pass  # Never call ClientThread.quit() here!

    def run(self):
        self.handler = self.createHandler()
        self.prepare()
        self.exec_()  # Wait for quit()
        self.finish()

    def _finished(self):  # Called when disconnected or manually
        self.server.connectionClosed(self.id)


class SocketHandler(QObject):
    def __init__(self, socket):
        QObject.__init__(self, socket)
        self.sockAdapter = SocketAdapter(socket, self)
        self.sockAdapter.messageReceived.connect(self.receiveRequest)

    # self.requestHandlers=collections.OrderedDict()
    # self.subHandlers=[]

    def handleRequest(self, requestId, description, data):
        raise NotImplementedError()

    # def handleRequest(self, requestId, description, data):
    # 	result=None
    # 	for regex in self.requestHandlers.keys():
    # 		if regex.fullmatch(description):
    # 			result=self.requestHandlers[regex](data)
    # 			break
    # 	for handler in self.subHandlers:
    # 		handler.handleRequest(description, data)
    # 	if result is not None:
    # 		self.sendResponse(requestId, result)
    #
    # def registerHandlerMethod(self, handlerMethod, descriptionRegExp, flags=0):
    # 	regex=re.compile(descriptionRegExp, flags=flags)
    # 	self.requestHandlers[regex]=handlerMethod
    #
    # def registerSubHandler(self, handler):
    # 	self.subHandlers.append(handler)

    def notify(self, description, data):
        print("Notify")
        newData = bytearray()
        stream = DataStream(newData)
        stream.writeBool(False)  # Data is notification
        stream.writeString(description)
        stream.writeByteArray(data)
        return self.sockAdapter.send(newData)

    def receiveRequest(self, data):
        stream = DataStream(data)
        self.handleRequest(stream.readUInt16(), stream.readString(),
                           stream.readByteArray())

    def sendResponse(self, requestId, data):
        newData = bytearray()
        stream = DataStream(newData)
        stream.writeBool(True)  # Data sent is request response
        stream.writeUInt16(requestId)
        stream.writeByteArray(data)
        return self.sockAdapter.send(newData)

    def socket(self):
        return self.sockAdapter.socket

    def setSocket(self, sock):
        self.sockAdapter.socket = sock

    socket = property(socket, setSocket)
