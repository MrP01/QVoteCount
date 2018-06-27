import errno
import os
import struct

from .base import (AbstractDatabaseEngine, AbstractContainerEngine,
                   ItemError, MetaItem)
from .datastream import DataStream
from .itemstorage import ItemStorage


class StorageEngine(AbstractDatabaseEngine):
    class ContainerEngine(AbstractContainerEngine, ItemStorage):
        def __init__(self, container):
            AbstractContainerEngine.__init__(self, container)
            ItemStorage.__init__(self)
            self._metas = {}

        def update(self):
            pass

        def addItem(self, item):
            item.id = ItemStorage.addItem(self, item)
            self._metas[item.id] = MetaItem(id=item.id,
                                            lastUpdate=self.container.database.currentDateTime())
            return item.id

        def addItems(self, items):
            for item in items:
                yield self.addItem(item)  # Since this is the fastest way anyways

        def insertItem(self, item):
            if item.id in self.itemIds():
                raise ItemError(item.id)
            ItemStorage.insertItem(self, item)
            self._metas[item.id] = MetaItem(id=item.id,
                                            lastUpdate=self.container.database.currentDateTime())

        def insertItems(self, items):
            for item in items:
                self.insertItem(item)

        def getItem(self, itemId):
            try:
                return ItemStorage.getItem(self, itemId)
            except KeyError:
                raise ItemError(itemId) from None

        def getItems(self, itemIds):
            for itemId in itemIds:
                yield self.getItem(itemId)

        def setItem(self, item):
            if item.id not in self.itemIds():
                raise ItemError(item.id)
            ItemStorage.setItem(self, item)
            self.metaItem(item.id).lastUpdate = self.container.database.currentDateTime()

        def setItems(self, items):
            for item in items:
                self.setItem(item)

        def removeItem(self, itemId):
            try:
                ItemStorage.removeItem(self, itemId)
            except KeyError:
                raise ItemError(itemId) from None
            self.metaItem(itemId).lastUpdate = self.container.database.currentDateTime()
            self.metaItem(itemId).deleted = True

        def removeItems(self, *itemIds):
            for itemId in itemIds:
                self.removeItem(itemId)

        def metaItem(self, itemId):
            return self._metas[itemId]

        def metaItems(self):
            return self._metas.values()

        def filterItems(self, check):
            return filter(check, self.allItems())

        def allItems(self):
            return ItemStorage.items(self)

        def itemIds(self):
            return ItemStorage.ids(self)

        def clear(self):
            ItemStorage.clear(self)
            self._metas.clear()

        def itemCount(self):
            return len(self._data)

        def checkItemExists(self, itemId):
            return itemId in self._data.keys()

        def nextItemId(self):
            try:
                return max(self._metas.keys()) + 1
            except ValueError:
                return 0

    def __init__(self):
        AbstractDatabaseEngine.__init__(self)
        self._clients = ItemStorage()
        self._filePath = ""

    def open(self, filePath):
        print("Load db")
        self._filePath = filePath
        if not os.path.exists(filePath):
            return True
        with open(filePath, "rb") as file:
            stream = DataStream(file.read())
        try:
            for container in self.database.containers:
                itemCount = stream.readUInt16()
                for i in range(itemCount):
                    item = container.entityCls.readItem(stream.device)
                    container.engine.insertItem(item)
        except struct.error:
            raise IOError(errno.ENOMEM) from None
        return False

    def close(self):
        data = bytearray()
        stream = DataStream(data)
        for container in self.database.containers:
            stream.writeUInt16(len(container))
            for item in container:
                container.entityCls.writeItem(stream.device, item)
        with open(self.filePath, "wb") as file:
            file.write(data)
        print("Data saved", len(data))

    def commit(self):
        pass

    def addClient(self, client):
        return self._clients.addItem(client)

    def getClient(self, clientId):
        return self._clients.getItem(clientId)

    def closeClient(self, clientId):
        self._clients.removeItem(clientId)

    def checkAccess(self):
        return True

    def createContainerEngine(self, container):
        return StorageEngine.ContainerEngine(container)

    @property
    def filePath(self):
        return self._filePath
