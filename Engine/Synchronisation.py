from PySide6.QtCore import *

from .DataStream import DataStream
from .Network import RequestHandler, Request


class SyncThread(QThread):  # For Clients
    def __init__(self, socket, database, parent=None):
        QThread.__init__(self, parent)
        self.socket = socket
        self.database = database
        self.lastUpdate = QDateTime()
        self.timer = QTimer()
        self.timer.timeout.connect(self.syncAll)

    def syncAll(self):
        for container in list(self.database.containers.values()):
            self.sync(container)

    def sync(self, container):
        print("Sync request")
        print(QThread.currentThread() == self)
        request = Request(self.socket("A"))
        stream = DataStream(request.data)
        stream.writeDateTime(self.lastUpdate)
        stream.writeString(container.tag)
        request.responseArrived.connect(self.syncResponse)
        request.send()

    def syncResponse(self, data):
        pass

    def run(self):
        self.timer.start()
        self.exec_()


class SyncHandler(RequestHandler):
    def __init__(self, socket, database):
        RequestHandler.__init__(self, socket)
        self.database = database

    def handleRequest(self, requestId, description, data):
        if description == "A":
            newData = self.syncRequest(data)
        self.sendResponse(requestId, newData)

    def syncRequest(self, data):
        stream = DataStream(data)
        newData = QByteArray()
        stream = DataStream(newData)
        lastUpdate = stream.readDateTime()
        container = self.database.containers[stream.readString()]
        for action in container.actions:
            if action.dateTime >= lastUpdate:
                stream.writeString(action.type)
                stream.write
                if action.type in [Action.Add, Action.Set]:
                    stream.write
