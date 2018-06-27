from PySide.QtCore import QObject
from PySide.QtGui import QWidget, QTabWidget

from Database.tools import Item, ItemStorage


class AppManager(QObject):
    def __init__(self, parent):
        QObject.__init__(self, parent)

        self.apps = ItemStorage()
        self.appWidget = QTabWidget()
        self.appWidget.setTabsClosable(True)
        self.appWidget.tabCloseRequested.connect(self.closeTab)

    def addApp(self, app):
        app.id = self.apps.addItem(app)
        return app.id

    def removeApp(self, appId):
        self.apps.removeItem(appId)

    def closeTab(self, index):
        self.appWidget.widget(index).quit()


class App(QWidget, Item):
    Tab, Dialog = list(range(2))

    def __init__(self, appManager, showingType=0, windowTitle=None, windowIcon=None):
        QWidget.__init__(self)
        Item.__init__(self)
        self.appManager = appManager
        self._showingType = showingType
        self._closingAllowed = False
        if windowTitle is not None:
            self.setWindowTitle(windowTitle)
        if windowIcon is not None:
            self.setWindowIcon(windowIcon)

    def start(self):  # Overwrite this
        self.display()

    def quit(self):  # Overwrite this
        self.cancel()
        self.delete()
        return True

    def display(self):
        if self.showingType() == App.Tab:
            self.appManager.appWidget.addTab(self, self.windowIcon(), self.windowTitle())
        elif self.showingType() == App.Dialog:
            self.show()
        self.setFocus()

    def cancel(self):
        if self._showingType == App.Tab:
            self.appManager.appWidget.removeTab(self.index())
        elif self._showingType == App.Dialog:
            self._closingAllowed = True
            self.close()

    def closeEvent(self, event):
        if self._closingAllowed:
            event.accept()
        else:
            self.quit()
            event.ignore()

    def paintEvent(self, event):
        self.paintBackground()
        event.accept()

    def paintBackground(self):
        pass

    def setShowingType(self, showingType):
        if showingType != self._showingType:
            if self.isVisible():
                self.cancel()
                self.setParent(None)
                self._showingType = showingType
                self.display()
            else:
                self._showingType = showingType

    def showingType(self):
        return self._showingType

    def setFocus(self):
        if self._showingType == App.Tab:
            self.appManager.appWidget.setCurrentWidget(self)
        elif self._showingType == App.Dialog:
            self.raise_()

    def setWindowTitle(self, title):
        QWidget.setWindowTitle(self, title)
        if self._showingType == App.Tab:
            self.appManager.appWidget.setTabText(self.index(), self.windowTitle())

    def setWindowIcon(self, icon):
        QWidget.setWindowIcon(self, icon)
        if self._showingType == App.Tab:
            self.appManager.appWidget.setTabIcon(self.index(), self.windowIcon())

    def index(self):
        return self.appManager.appWidget.indexOf(self)

    def delete(self):
        self.appManager.removeApp(self.id)
        self.deleteLater()


class ItemApp(App):
    EditMode, ReadMode = list(range(2))

    def __init__(self, mainManager, mode=None, showingType=0):
        App.__init__(self, mainManager, showingType)
        self.mode = mode
# ~ self.dirty=False
# ~ self.itemId=-1

# ~ class Applet(QWidget, Item):
# ~ def __init__(self, mainWindow, name):
# ~ QWidget.__init__(self)
# ~ self.mainWindow=mainWindow
# ~ self.dockWidget=QDockWidget(self.appManager.mainManager.)
