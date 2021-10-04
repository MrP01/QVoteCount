from PySide6.QtCore import *
from PySide6.QtWidgets import *

from .QtUIWrapper import QtModelWrapper
from .UI import createAction


class SortFilterProxyModel(QSortFilterProxyModel):  # Only for QtModelWrapper models
    def filterAcceptsRow(self, row, parent=None):
        source = self.sourceModel()
        for col in range(source.columnCount()):
            data = source.data(source.index(row, col, parent), self.filterRole())
            if (data is not None) and (self.filterRegExp().indexIn(str(data).lower()) >= 0):
                return True
        return False

# def lessThan(self, left, right):
# 	if left.column() != right.column():
# 		print("Cols not equal (SortFilterProxyModel)")
# 		return False
# 	return self.sourceModel().lessThan(left.row(),right.column(),left.column())
# return len(self.sourceModel().data(left)) < len(self.sourceModel().data(right))


class TableView(QTableView):
    def __init__(self, containerView):
        QTableView.__init__(self, containerView)
        self.containerView = containerView
        self.createActions()
        self.setContextMenuPolicy(Qt.ActionsContextMenu)

    def createActions(self):
        createAction(self, "Delete", self.deleteSelectedItems)

    def selectedItems(self):
        itemIds = set()  # No duplicates
        for index in self.selectedIndexes():
            itemIds.add(self.containerView.modelWrapper.idByIndex(self.model().
                                                                  mapToSource(index)))
        return itemIds

    def deleteSelectedItems(self):
        # with self.containerView.modelWrapper.modelAccessClient:
        for itemId in self.selectedItems():
            self.containerView.container.removeItem(itemId)


class ContainerView(QWidget):
    itemDoubleClicked = Signal(int)

    def __init__(self, container=None, modelWrapper=None, parent=None):
        QWidget.__init__(self, parent)
        self._container = None
        self._modelWrapper = None
        self.proxyModel = SortFilterProxyModel()
        self.proxyModel.rowsInserted.connect(self.updateLen)
        self.proxyModel.rowsRemoved.connect(self.updateLen)

        self.initUI()
        self.nameScheme = "{name} ({count} items)"
        self.setEnabled(False)
        if container is not None:
            self.setContainer(container, modelWrapper)

    def initUI(self):
        label = QLabel("Not available")
        label.setAlignment(Qt.AlignHCenter | Qt.AlignVCenter)

        self.nameLabel = QLabel()
        self.updateButton = QPushButton("Update")
        self.filterEdit = QLineEdit()
        self.tableView = TableView(self)
        self.tableView.setModel(self.proxyModel)
        self.tableView.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tableView.setSortingEnabled(False)  # Todo (SortFilterModel not working correctly)
        self.tableView.doubleClicked.connect(self.handleDblClick)

        layout = QStackedLayout()
        layout.addWidget(label)
        availableWidget = QWidget()
        availableLayout = QGridLayout()
        availableLayout.addWidget(self.nameLabel, 0, 0)
        availableLayout.addWidget(self.updateButton, 0, 1)
        availableLayout.addWidget(self.filterEdit, 0, 2)
        availableLayout.addWidget(self.tableView, 1, 0, 1, 3)
        availableWidget.setLayout(availableLayout)
        layout.addWidget(availableWidget)
        self.setLayout(layout)

        self.filterEdit.returnPressed.connect(self.updateFilter)

    def setContainer(self, container, modelWrapper=None):
        self._container = container
        self._modelWrapper = modelWrapper
        if self._modelWrapper is None:
            self._modelWrapper = QtModelWrapper(self.container)
            self.container.addEventFilter(self.modelWrapper)
        self.updateLen()
        self.updateButton.clicked.connect(self.updateContainer)
        self.proxyModel.setSourceModel(self._modelWrapper)
        self.tableView.resizeColumnsToContents()
        self.modelWrapper.availabilityChanged.connect(self.updateAvailability)
        self.updateContainer()
        self.updateAvailability()
        self.setEnabled(True)

    @property
    def container(self):
        return self._container

    @property
    def modelWrapper(self):
        return self._modelWrapper

    def updateContainer(self):
        self.updateButton.setEnabled(False)
        self.container.update()
        self.modelWrapper.repopulateModel()
        self.updateLen()
        self.updateAvailability()
        self.tableView.resizeColumnsToContents()
        self.updateButton.setEnabled(True)

    def updateAvailability(self):
        self.layout().setCurrentIndex(self.modelWrapper.isAvailable())

    def updateFilter(self):
        self.proxyModel.setFilterWildcard(self.filterEdit.text().lower())

    def updateLen(self):
        # with self.modelWrapper.modelAccessClient:
        self.nameLabel.setText(self.nameScheme.format(name=str(self.container), count=len(self.container)))

    def handleDblClick(self, index):
        self.itemDoubleClicked.emit(self._modelWrapper.idByIndex(self.proxyModel.mapToSource(index)))

    def nameScheme(self):
        return self._scheme

    def setNameScheme(self, scheme):
        if not isinstance(scheme, str):
            raise TypeError("Scheme must be str")
        self._scheme = scheme

    nameScheme = property(nameScheme, setNameScheme)
