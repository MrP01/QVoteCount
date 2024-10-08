from PySide6.QtCore import *
from PySide6.QtNetwork import QAbstractSocket
from base.StorageEngine import *
from base.UADatabase import *
from base.dataStream import DataStream

from .Network import Request, NetworkError


class Signature(object):
    Open = "OPEN"
    Close = "CLOSE"
    AddConnection = "ADD_CONNECTION"
    CloseConnection = "CLOSE_CONNECTION"
    UpdateContainer = "A"
    AddItem = "B"
    InsertItem = "C"
    SetItem = "D"
    RemoveItem = "E"


class VDBEngine(StorageEngine):
    def __init__(self, office, database=None):
        StorageEngine.__init__(self, database)
        self.postOffice = office

    def open(self):
        request = Request(self.postOffice, Signature.Open)
        stream = DataStream(request.data)
        stream.writeString(self.database.password)
        request.send()
        StorageEngine.open(self)
        request.waitForResponse()
        stream = DataStream(request.response)
        if not stream.readBool():
            raise IncorrectPasswordError()

    def close(self):
        request = Request(self.postOffice, Signature.Close)
        request.send()
        StorageEngine.close(self)
        request.waitForResponse()

    def addConnection(self, connection):
        request = Request(self.postOffice, Signature.AddConnection)
        stream = DataStream(request.data)
        stream.writeString(connection.user.name)
        stream.writeString(connection.user.password)
        request.send()
        request.waitForResponse()
        stream = DataStream(request.response)
        if stream.readBool():
            return StorageEngine.addConnection(self, connection)
        else:
            raise AuthenticationError()

    def closeConnection(self, connectionId):
        request = Request(self.postOffice, Signature.CloseConnection)
        stream = DataStream(request.data)
        stream.writeUInt16(connectionId)
        request.send()
        request.waitForResponse()
        stream = DataStream(request.response)
        if not stream.readBool():
            raise IncorrectPasswordError()

    def createContainerEngine(self, container):
        return VDBContainerEngine(self.postOffice, container)

    def checkAccess(self):
        if not (self.postOffice.socket.state() == QAbstractSocket.ConnectedState):
            raise NetworkError(NetworkError.NotConnected)


class VDBContainerEngine(StorageContainerEngine):
    def __init__(self, office, container=None):
        StorageContainerEngine.__init__(self, container)
        self.postOffice = office

    # ~ def update(self):
    # ~ print("Updating %s"%self.container.name)
    # ~ request=Request(self.postOffice, chr(self.container.id)+"A")
    # ~ stream=DataStream(request.data)
    # ~ stream.writeDateTime(self.lastUpdate)
    # ~ request.send()
    # ~ request.waitForResponse()
    # ~ stream=DataStream(request.response)
    # ~ logLen=stream.readUInt16()
    # ~ for i in range(logLen):
    # ~ log=self.container.readLog(stream)
    # ~ if log.type == LogEntry.Clear:
    # ~ self.container.clear()
    # ~ elif log.type == ItemLogEntry.Add:
    # ~ item=self.container.readItem(stream)
    # ~ self.container.addItem(item)
    # ~ elif log.type == ItemLogEntry.Set:
    # ~ item=self.container.readItem(stream)
    # ~ self.container.setItem(item)
    # ~ elif log.type == ItemLogEntry.Remove:
    # ~ self.container.removeItem(log.itemId)
    # ~ self.lastUpdate=stream.readDateTime()
    # ~ print("...done, LastUpdate:", self.lastUpdate.toString())

    def update(self):
        print("Updating {}".format(self.container.name))
        request = Request(self.postOffice, chr(self.container.id) + Signature.UpdateContainer)
        stream = DataStream(request.data)
        for meta in StorageContainerEngine.metaItems(self):
            MetaItem.writeItem(request.data, meta)
        request.send()
        request.waitForResponse()
        stream = DataStream(request.response)
        updateLen = stream.readUInt16()
        for i in range(updateLen):
            meta = MetaItem.readItem(request.response)
            if meta.deleted:
                if meta not in self.metas():
                    continue  # Just don't care
                StorageContainerEngine.removeItem(self, meta.itemId)
            else:
                item = self.container.entityCls.readItem(request.response)
                if item in self.container:
                    StorageContainerEngine.setItem(self, item)
                else:
                    StorageContainerEngine.insertItem(self, item)
            self.meta(meta.itemId).lastUpdate = meta.lastUpdate
        self.lastUpdate = stream.readDateTime()

    def addItem(self, item):
        request = Request(self.postOffice, chr(self.container.id) + Signature.AddItem)
        stream = DataStream(request.data)
        stream.writeUInt8(self.container.currentConnection.id)
        self.container.entityCls.writeItem(request.data, item)
        request.send()
        connection = self.container.currentConnection
        connection.releaseDb()
        request.waitForResponse()
        connection.acquireDb()
        stream = DataStream(request.response)
        if not stream.readBool():
            raise self.readDBError(stream)
        item.id = stream.readUInt16()
        try:
            StorageContainerEngine.insertItem(self, item)
        except ItemError:
            self.update()
        return item.id

    def setItem(self, item):
        request = Request(self.postOffice, chr(self.container.id) + Signature.SetItem)
        stream = DataStream(request.data)
        stream.writeUInt8(self.container.currentConnection.id)
        self.container.entityCls.writeItem(request.data, item)
        request.send()
        connection = self.container.currentConnection
        connection.releaseDb()
        request.waitForResponse()
        connection.acquireDb()
        stream = DataStream(request.response)
        if not stream.readBool():
            raise self.readDBError(stream)
        StorageContainerEngine.setItem(self, item)

    def removeItem(self, itemId):
        connection = self.container.currentConnection
        request = Request(self.postOffice, chr(self.container.id) + Signature.RemoveItem)
        stream = DataStream(request.data)
        stream.writeUInt8(connection.id)
        stream.writeUInt16(itemId)
        request.send()
        connection.releaseDb()
        request.waitForResponse()
        connection.acquireDb()
        print("Remove Response", request.response)
        stream = DataStream(request.response)
        if not stream.readBool():
            raise self.readDBError(stream)
        StorageContainerEngine.removeItem(self, itemId)

    @staticmethod
    def readDBError(stream):
        errType = stream.readString()
        if errType == "A":
            return AuthenticationError()
        elif errType == "B":
            return PermissionError()
        elif errType == "C":
            return ItemError()
        elif errType == "D":
            return AccessError(int(stream.readString()))

    def clear(self):
        raise NotImplementedError("Virtual clearing not provided.")


class VCRequestHandler(QObject):
    def __init__(self, database):
        QObject.__init__(self)
        self.database = database
        self.handlers = dict()
        self.connections = list()
        self.open = False
        for container in self.database.containers.allItems():
            self.handlers[chr(container.id)] = VCContainerRequestHandler(self, container)

    def handleRequest(self, description, data):
        if description == Signature.Open:
            return self.openRequest(data)
        elif description == Signature.Close:
            return self.closeRequest(data)
        elif description == Signature.AddConnection:
            return self.addConnectionRequest(data)
        elif description == Signature.CloseConnection:
            return self.closeConnectionRequest(data)
        else:
            return self.handlers[description[0]].handleRequest(description[1:], data)

    # def handleRequest(self, description, data):
    # 	print("Handle Request", description, data)
    # 	if not RequestHandler.handleRequest(self, description, data):
    # 		if self.open:
    # 			return self.handlers[description[0]].handleRequest(
    # 			description[1:], data)
    # 		else:
    # 			return bytearray()

    def openRequest(self, data):
        stream = DataStream(data)
        password = stream.readString()
        stream = DataStream()
        if password == self.database.password:
            self.open = True
            stream.writeBool(True)
        else:
            stream.writeBool(False)
        return stream.device

    def closeRequest(self, data):
        self.open = False
        for connectionId in self.connections:
            self.database.closeConnection(connectionId)
        return bytearray()

    def addConnectionRequest(self, data):
        stream = DataStream(data)
        userName = stream.readString()
        password = stream.readString()
        response = bytearray()
        stream = DataStream(response)
        try:
            user = self.database.checkUser(userName, password)
            connection = UAConnection(self.database, user)
            connectionId = self.database.addConnection(connection)
            self.connections.append(connectionId)
            stream.writeBool(True)
            stream.writeUInt16(connectionId)
        except AuthenticationError:
            stream.writeBool(False)
        return response

    def closeConnectionRequest(self, data):
        stream = DataStream(data)
        connectionId = stream.readUInt16()
        self.database.closeConnection(connectionId)
        return bytearray()

    def accessError(self, data):
        response = bytearray()
        # ~ response.write
        return response


class VCContainerRequestHandler(QObject):
    def __init__(self, mainHandler, container):
        QObject.__init__(self)
        self.mainHandler = mainHandler
        self.container = container

    def handleRequest(self, description, data):
        response = bytearray()
        if description[0] == "A":
            response = self.updateRequest(data)
        elif description[0] == "B":
            response = self.addItemRequest(data)
        elif description[0] == "C":
            response = self.setItemRequest(data)
        elif description[0] == "D":
            response = self.removeItemRequest(data)
        return response

    @staticmethod
    def writeDBError(device, error):
        if type(error) == AuthenticationError:
            DataStream.writeString(device, "A")
        elif type(error) == PermissionError:
            DataStream.writeString(device, "B")
        elif type(error) == ItemError:
            DataStream.writeString(device, "C")
        elif type(error) == AccessError:
            DataStream.writeString(device, "D")
            DataStream.writeUInt8(device, error.errno)
        else:
            print("Other Error occurred:", error)

    # ~ def updateRequest(self, data):
    # ~ print("UpdateRequest:{0}, currently having {1} items".
    # ~ format(self.container.name, len(self.container)))
    # ~ stream=DataStream(data)
    # ~ lastUpdate=stream.readDateTime()
    # ~ response=bytearray()
    # ~ stream=DataStream(response)
    # ~ removeLogs=self.container.logBook.select(lambda log:
    # ~ (log.type == ItemLogEntry.Remove) and (log.datetime >= lastUpdate))
    # ~ stream.writeUInt16(len(removeLogs))
    # ~ for log in notDoneLogs:
    # ~ if log.type not in (LogEntry.Clear, ItemLogEntry.Add, ItemLogEntry.Set,
    # ~ ItemLogEntry.Remove): continue
    # ~ self.container.writeLog(log, stream)
    # ~ if log.type in (ItemLogEntry.Add, ItemLogEntry.Set):
    # ~ self.container.writeItem(stream, self.container.getItem(log.itemId))
    # ~ stream.writeDateTime(self.container.database.currentDateTime())
    # ~ return response

    def updateRequest(self, data):
        stream = DataStream(data)
        lastUpdate = stream.readDateTime()
        response = bytearray()
        stream = DataStream(response)
        metas = tuple(filter(lambda meta: meta.lastUpdate >= lastUpdate, self.container.metaItems()))
        stream.writeUInt16(len(metas))
        for meta in metas:
            MetaItem.writeItem(response, meta)
            if not meta.deleted:
                self.container.entityCls.writeItem(response, self.container.engine.getItem(meta.itemId))
        stream.writeDateTime(self.container.database.currentDateTime())
        return response

    def addItemRequest(self, data):
        stream = DataStream(data)
        connection = self.container.database.getConnection(stream.readUInt8())
        item = self.container.entityCls.readItem(data)
        response = bytearray()
        stream = DataStream(response)
        try:
            with connection:
                myItemId = self.container.addItem(item)
            stream.writeBool(True)
            stream.writeUInt16(myItemId)
        except DatabaseError as error:
            stream.writeBool(False)
            self.writeDBError(response, error)
        return response

    def setItemRequest(self, data):
        stream = DataStream(data)
        connection = self.container.database.getConnection(stream.readUInt8())
        item = self.container.entityCls.readItem(data)
        response = bytearray()
        stream = DataStream(response)
        try:
            with connection:
                self.container.setItem(item)
            stream.writeBool(True)
        except DatabaseError as error:
            stream.writeBool(False)
            self.writeDBError(stream, error)
        return response

    def removeItemRequest(self, data):
        stream = DataStream(data)
        connection = self.container.database.getConnection(stream.readUInt8())
        itemId = stream.readUInt16()
        response = bytearray()
        stream = DataStream(response)
        try:
            with connection:
                self.container.removeItem(itemId)
            stream.writeBool(True)
        except DatabaseError as error:
            stream.writeBool(False)
            self.writeDBError(stream, error)
        return response
