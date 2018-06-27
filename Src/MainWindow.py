from PySide.QtCore import QByteArray

from Engine.MainWindow import MainWindow


class MyMainWindow(MainWindow):
    def __init__(self, mainManager):
        MainWindow.__init__(self)
        self.mainManager = mainManager
        self.setWindowTitle("SchulSprecherWahl by Peter Waldert")
        self.closeRequested.connect(self.mainManager.quit)
        self.setCentralWidget(self.mainManager.appManager.appWidget)

    def start(self, data):
        self.restoreGeometry(QByteArray(bytes(data)))
        self.show()
        return True

    def quit(self):
        self.cancel()
        return self.saveGeometry().data()
