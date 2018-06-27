from PySide.QtNetwork import QSslSocket

from .DataStream import DataStream
from .ItemStorage import ItemStorage, Item
from .Network import *


class ClientSocket(QSslSocket):
    def __init__(self, parent=None):
        QSslSocket.__init__(self, parent)
        self.requests = ItemStorage()
        self.nextBlockSize = 0
        self.readyRead.connect(self.receiveResponse)

    def issueRequest(self, request):
        if self.state() != QAbstractSocket.ConnectedState:
            raise NetworkError(NetworkError.NotConnected)
        self.requests.addItem(request)
        array = QByteArray()
        stream = DataStream(array)  # , QIODevice.WriteOnly
        stream.writeUInt16(0)
        stream.writeInt(request.id)
        stream.writeString(request.description)
        stream.writeByteArray(request.data)
        stream.device().seek(0)
        stream.writeUInt16(array.size() - SIZEOF_UINT16)
        self.write(array)
        self.waitForBytesWritten()

    def receiveResponse(self):
        stream = DataStream(self)
        while True:
            if (self.nextBlockSize == 0) and (self.bytesAvailable() >= SIZEOF_UINT16):
                self.nextBlockSize = stream.readUInt16()
            if self.bytesAvailable() >= self.nextBlockSize:
                break
        request = self.requests.getItem(stream.readInt())
        request.receiveResponse(stream.readByteArray())
        self.removeRequest(request.id)
        self.nextBlockSize = 0

    def removeRequest(self, id):
        self.requests.removeItem(id)


class Server(QTcpServer):
    def __init__(self, certificate, defaultPrivateKey, parent=None):
        QTcpServer.__init__(self, parent)
        self.certificate = certificate
        self.defaultPrivateKey = defaultPrivateKey
        self.clients = ItemStorage()

    def incomingConnection(self, socketId):
        clientThread = ClientThread(self, socketId)
        self.addClient(clientThread)
        clientThread.start()

    def connectionClosed(self, clientThread):
        self.removeClient(clientThread.id)

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
        self.socketId = socketId
        self.socket = None

    def createSocket(self, socketId):
        self.socket = ServerSocket(socketId, self.server.certificate, self.createPrivateKey())
        self.socket.setHandler(self.createHandler(self.socket))

    def createHandler(self, socket):
        return RequestHandler(socket)

    def createPrivateKey(self):
        return self.server.defaultPrivateKey

    def connected(self):
        pass

    def encrypted(self):
        pass

    def sslErrors(self, errors):
        pass

    def socketError(self, error):
        pass

    def prepare(self):  # Executed in Thread before handling
        self.socket.connected.connect(self.connected)
        self.socket.encrypted.connect(self.encrypted)
        self.socket._error.connect(self.socketError)
        self.socket._sslErrors.connect(self.sslErrors)
        self.socket.disconnected.connect(self.quit)

    def finish(self):  # Executed in Thread after disconnected
        pass  # Never call ClientThread.quit() here!

    def run(self):
        self.createSocket(self.socketId)
        self.socket.startServerEncryption()
        self.prepare()
        self.exec_()  # Wait for quit()
        self.finish()

    def quit(self):  # Called when disconnected or manually
        self.exit(not self.socket.state() == ServerSocket.ConnectedState)
        self.wait()
        self.server.connectionClosed(self)


class ServerSocket(QSslSocket):
    _sslErrors = Signal(list)
    _error = Signal(int)

    def __init__(self, socketId, certificate, privateKey, handler=None, parent=None):
        QSslSocket.__init__(self, parent)
        self.setLocalCertificate(certificate)
        self.setPrivateKey(privateKey)
        self.handler = handler
        self.nextBlockSize = 0
        if not self.setSocketDescriptor(socketId):
            raise NetworkError()
        self.readyRead.connect(self.receiveRequest)
        self.sslErrors.connect(self._sslErrors)
        self.error.connect(self._error)

    def __sslErrors(self, errors):
        self._sslErrors.emit(errors)

    def __error(self, error):
        self._error.emit(error)

    def setHandler(self, handler):
        self.handler = handler

    def receiveRequest(self):
        stream = DataStream(self)
        while True:
            if (self.nextBlockSize == 0) and (self.bytesAvailable() >= SIZEOF_UINT16):
                self.nextBlockSize = stream.readUInt16()
            if self.bytesAvailable() >= self.nextBlockSize:
                break
        self.handler.handleRequest(stream.readInt(), stream.readString(), stream.readByteArray())
        self.nextBlockSize = 0

    def sendResponse(self, requestId, data):
        array = QByteArray()
        stream = DataStream(array)  # , QIODevice.WriteOnly
        stream.writeUInt16(0)
        stream.writeInt(requestId)
        stream.writeByteArray(data)
        stream.device().seek(0)
        stream.writeUInt16(array.size() - SIZEOF_UINT16)
        self.write(array)
        self.waitForBytesWritten()
