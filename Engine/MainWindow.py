from PySide6.QtCore import Qt, Signal, QTimer, QEventLoop
from PySide6.QtWidgets import QMainWindow, QFrame, QAction, QIcon, QPainter


class PopupDialog(QFrame):
    Rejected, Accepted = list(range(2))
    closed = Signal()
    accepted = Signal()
    rejected = Signal()

    def __init__(self, mainWindow):
        QFrame.__init__(self, mainWindow)
        self.mainWindow = mainWindow
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        # self.setWindowModality(Qt.WindowModal)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self._returnCode = None

    def popup(self):
        self.mainWindow.activateWindow()
        self.show()
        self.mainWindow.addPopup(self)
        self.updatePosition()

    def cancel(self):
        if self in self.mainWindow.currentPopups:
            self.mainWindow.removePopup(self)
            self.closed.emit()
            self.close()

    def updatePosition(self):
        rect = self.geometry()
        if (len(self.mainWindow.currentPopups) > 1) and (self.mainWindow.currentPopups[-2] != self):
            rect.moveTopRight(self.mainWindow.currentPopups[-2].geometry().bottomRight())
        else:
            rect.moveTopRight(self.mainWindow.mapToGlobal(self.mainWindow.centralWidget().geometry().topRight()))
        self.move(rect.topLeft())

    def reject(self):
        self._returnCode = PopupDialog.Rejected
        self.cancel()
        self.rejected.emit()

    def accept(self):
        self._returnCode = PopupDialog.Accepted
        self.cancel()
        self.accepted.emit()

    def exec_(self):
        if not self.isVisible():
            self.popup()
        loop = QEventLoop()
        self.closed.connect(loop.quit)
        loop.exec_()
        return self._returnCode

    def flash(self):
        pass  # Todo

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.cancel()
            event.accept()
            return
        event.ignore()

    def paintEvent(self, event):
        self.paintBackground()
        event.accept()

    def paintBackground(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        self.drawFrame(painter)


# ~ def closeEvent(self, event):
# ~ if self._closingAllowed:
# ~ QFrame.closeEvent(self, event)
# ~ else:
# ~ self.reject()
# ~ event.ignore()

class MainWindow(QMainWindow):
    closeRequested = Signal()

    def __init__(self, parent=None):
        QMainWindow.__init__(self, parent)
        self._closingAllowed = False
        self._altPressed = False
        self.iconPath = str()
        self.currentPopups = list()

    def cancel(self):
        self._closingAllowed = True
        QTimer.singleShot(0, self.close)

    def addPopup(self, popup):
        self.currentPopups.append(popup)

    def removePopup(self, popup):
        self.currentPopups.remove(popup)
        self.updatePopupPositions()

    def closeEvent(self, event):
        if self._closingAllowed:
            QMainWindow.closeEvent(self, event)
        else:
            self.closeRequested.emit()
            event.ignore()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Alt:
            self._altPressed = True
            event.accept()
        else:
            event.ignore()

    def keyReleaseEvent(self, event):
        if event.key() == Qt.Key_Alt and self._altPressed:
            self.menuBar().setVisible(not self.menuBar().isVisible())
            self.menuBar().setFocus()
            event.accept()
        else:
            event.ignore()

    def moveEvent(self, event):
        QMainWindow.moveEvent(self, event)
        self.updatePopupPositions()

    def resizeEvent(self, event):
        QMainWindow.resizeEvent(self, event)
        self.updatePopupPositions()

    def updatePopupPositions(self):
        for popup in reversed(self.currentPopups):
            popup.updatePosition()

    def setEnabled(self, enabled):
        for action in self.actions():
            action.setEnabled(enabled)
        self.centralWidget().setEnabled(enabled)

    def setIconPath(self, path):
        self.iconPath = path

    def createAction(self, text, slot=None, shortcut=None, icon=None, tip=None, checkable=False):
        action = QAction(text, self)
        if icon is not None:
            action.setIcon(QIcon(self.iconPath + "/" + icon))
        if shortcut is not None:
            action.setShortcut(shortcut)
        if tip is not None:
            action.setToolTip(tip)
            action.setStatusTip(tip)
        if slot is not None:
            action.triggered.connect(slot)
        if checkable:
            action.setCheckable(True)
        self.addAction(action)
        return action
