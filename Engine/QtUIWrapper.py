from PySide.QtCore import QAbstractTableModel, QModelIndex, Qt, Signal

from Database.core import (AbstractContainerEventFilter, ReferenceAttribute,
                           AddItemEvent, AddItemsEvent, InsertItemEvent, SetItemEvent, RemoveItemEvent,
                           ClearEvent, UpdateEvent, AbstractItemEvent)


class QtModelWrapper(AbstractContainerEventFilter, QAbstractTableModel):
    availabilityChanged = Signal(bool)

    def __init__(self, container=None):
        AbstractContainerEventFilter.__init__(self, container)
        QAbstractTableModel.__init__(self)
        # self.modelAccessClient=None
        self._headers = {}
        self._referenceContainers = {}
        for col, (name, attr) in enumerate(container.entityCls.attributes.items()):
            self._headers[col] = name
            if isinstance(attr, ReferenceAttribute):
                self._referenceContainers[col] = next(filter(lambda c: c.entityCls == attr.entityCls,
                                                             self.container.database.containers.values()))
        self._idsByRows = {}

    def filterEvent(self, event):
        if isinstance(event, AbstractItemEvent):
            if isinstance(event, AddItemEvent):
                self.addItemEvent(event)
            elif isinstance(event, InsertItemEvent):
                self.insertItemEvent(event)
            elif isinstance(event, SetItemEvent):
                self.setItemEvent(event)
            elif isinstance(event, RemoveItemEvent):
                self.removeItemEvent(event)
        elif isinstance(event, AddItemsEvent):
            self.addItemsEvent(event)
        elif isinstance(event, UpdateEvent):
            self.updateEvent(event)
        elif isinstance(event, ClearEvent):
            self.clearEvent(event)

    def addItemEvent(self, event):
        # cli=self.container.currentClient
        # cli.releaseDb()
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._idsByRows[self.rowCount()] = event.itemId
        self.endInsertRows()

    # cli.acquireDb()

    def addItemsEvent(self, event):
        rowCount = self.rowCount()
        self.beginInsertRows(QModelIndex(), rowCount, rowCount + len(event.itemIds))
        for row, itemId in enumerate(event.itemIds, rowCount):
            self._idsByRows[row] = itemId
        self.endInsertRows()

    def insertItemEvent(self, event):
        self.beginInsertRows(QModelIndex(), self.rowCount(), self.rowCount())
        self._idsByRows[self.rowCount()] = event.itemId
        self.endInsertRows()

    def setItemEvent(self, event):
        row = self.rowById(event.itemId)
        self.dataChanged.emit(self.index(row, 0),
                              self.index(row, self.columnCount() - 1))

    def removeItemEvent(self, event):
        row = self.rowById(event.itemId)
        self.beginRemoveRows(QModelIndex(), row, row)
        self.updateIdsByRows()  # Todo (only reposition items after that one)
        self.endRemoveRows()

    def updateEvent(self, event):
        self.repopulateModel()

    def clearEvent(self, event):
        self.reset()

    # def modelAccessClient(self):
    # 	return self._modelAccessClient
    # def setModelAccessClient(self, client):
    # 	self._modelAccessClient=client
    # 	self.updateAvailability()
    # modelAccessClient=property(modelAccessClient, setModelAccessClient)

    def isAvailable(self):
        # if self.modelAccessClient is None:
        # 	return False
        return True

    def updateAvailability(self):
        self.availabilityChanged.emit(self.isAvailable())

    def repopulateModel(self):
        self.updateIdsByRows()
        self.reset()

    def rowCount(self, parent=QModelIndex()):
        return len(self._idsByRows)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def lessThan(self, row1, row2, col):
        # with self.modelAccessClient:
        v1, v2 = (getattr(self.container.getItem(self.idByRow(row)), self._headers[col]) for row in (row1, row2))
        ret = self.container.entityCls.attributes[self._headers[col]].lessThan(v1, v2)
        print("LessThan", col, v1, v2, ret)
        return ret

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]

    def data(self, index, role=Qt.DisplayRole):
        # if (self.modelAccessClient is None) or (not index.isValid()):
        if not index.isValid():
            return
        if role == Qt.DisplayRole:
            item = self.itemByIndex(index)
            return self.getItemData(item, index.column())
        elif role == Qt.UserRole:
            return self.idByRow(index.row())

    def setData(self, index, value, role=Qt.EditRole):  # Todo
        return False

    def sort(self, col, order):
        pass

    def flags(self, index=QModelIndex()):
        return Qt.ItemIsEnabled | Qt.ItemIsSelectable

    def getItemData(self, item, col):
        attr = self.container.entityCls.attributes[self._headers[col]]
        if isinstance(attr, ReferenceAttribute):
            ref_item = getattr(item, self._headers[col])
            if ref_item is None:
                return "-"
            return str(ref_item)
        return attr.reprValue(getattr(item, self._headers[col]))

    def updateIdsByRows(self):
        self._idsByRows.clear()
        for row, itemId in enumerate(self.container.itemIds()):
            self._idsByRows[row] = itemId

    def idByRow(self, row):
        return self._idsByRows[row]

    def rowById(self, itemId):
        for row in list(self._idsByRows.keys()):
            if self.idByRow(row) == itemId:
                return row
        raise KeyError("Item not in table.")

    def idByIndex(self, index):
        return self._idsByRows[index.row()]

    def itemByRow(self, row):
        return self.container.getItem(self.idByRow(row))

    def itemByIndex(self, index):
        return self.container.getItem(self.idByIndex(index))
