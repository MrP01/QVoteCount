from PySide6.QtCore import QDateTime, QDate
from PySide6.QtGui import QAction
from PySide6.QtWidgets import *


def BLayoutHelper(*items, orientation=QBoxLayout.LeftToRight):
    layout = QBoxLayout(orientation)
    for item in items:
        if item is None:
            layout.addStretch()
        elif isinstance(item, QWidget):
            layout.addWidget(item)
        elif isinstance(item, QLayout):
            layout.addLayout(item)
        elif isinstance(item, tuple):
            if isinstance(item[0], QWidget):
                layout.addWidget(item[0], item[1])
            if isinstance(item[0], QLayout):
                layout.addLayout(item[0], item[1])
    return layout


class AppLayout(QFormLayout):
    def __init__(self, parent=None):
        QFormLayout.__init__(self, parent)

    def addButtonBar(self, *buttons):
        self.addRow(BLayoutHelper(None, *buttons))


class SimpleTextList(QGroupBox):
    def __init__(self, title, items=(), parent=None):
        QGroupBox.__init__(self, parent)
        self.setTitle(title)
        self.listWidget = QListWidget(self)
        for item in items:
            self.listWidget.addItem(QListWidgetItem(item))
        self.itemEdit = QLineEdit(self)
        self.addButton = QPushButton("&Add", self)  # Todo: translation
        self.removeButton = QPushButton("&Remove", self)
        layout = QGridLayout()
        layout.addWidget(self.itemEdit, 0, 0, 1, 2)
        layout.addWidget(self.listWidget, 1, 0)
        layout.addLayout(
            BLayoutHelper(self.addButton, self.removeButton, None, orientation=QBoxLayout.TopToBottom), 1, 1
        )
        self.setLayout(layout)
        self.itemEdit.returnPressed.connect(self.addItem)
        self.addButton.clicked.connect(self.addItem)
        self.removeButton.clicked.connect(self.removeSelectedItem)

    def addItem(self):
        if len(self.itemEdit.text()) > 0:
            self.listWidget.addItem(QListWidgetItem(self.itemEdit.text()))
            self.itemEdit.clear()

    def removeSelectedItem(self):
        self.listWidget.takeItem(self.listWidget.currentRow())

    def allItems(self):
        return [self.listWidget.item(row).text() for row in range(self.listWidget.count())]


def createAction(parent, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
    action = QAction(text, parent)
    if icon is not None:
        action.setIcon(QIcon(icon))
    if shortcut is not None:
        action.setShortcut(shortcut)
    if tip is not None:
        action.setToolTip(tip)
        action.setStatusTip(tip)
    if slot is not None:
        action.triggered.connect(slot)
    if checkable:
        action.setCheckable(True)
    parent.addAction(action)
    return action


def labelWidget(text, widget):
    label = QLabel(text)
    label.setBuddy(widget)
    return label, widget


def createLabelledLineEdit(text, placeholder="", prompt=""):
    label, lineEdit = labelWidget(text, QLineEdit(prompt))
    lineEdit.setPlaceholderText(placeholder)
    # ~ lineEdit.selectAll()
    return label, lineEdit


def createLabelledDateTimeEdit(text, datetime=QDateTime()):
    label, datetimeEdit = labelWidget(text, QDateTimeEdit())
    datetimeEdit.setDateTime(datetime)
    return label, datetimeEdit


def createLabelledDateEdit(text, date=QDate()):
    label, dateEdit = labelWidget(text, QDateEdit())
    dateEdit.setDate(date)
    return label, dateEdit


def createLabelledSpinBox(text, value=0, suffix="", _min=0, _max=100):
    label, spinBox = labelWidget(text, QSpinBox())
    spinBox.setSuffix(suffix)
    spinBox.setRange(_min, _max)
    spinBox.setValue(value)
    return label, spinBox


def createLabelledRadioButton(text, buttonText):
    return labelWidget(text, QRadioButton(buttonText))


def createLabelledLabel(text, labelText, frameStyle=QFrame.NoFrame):
    label, label2 = labelWidget(text, QLabel(labelText))
    label2.setFrameStyle(frameStyle)
    return label, label2
