from PySide.QtCore import QObject

from Engine.StartQuitAssistant import StartQuitAssistant
from .AppManager import MyAppManager
from .DatabaseManager import DbManager
from .MainWindow import MyMainWindow


class MainManager(QObject):
    def __init__(self, parent=None):
        QObject.__init__(self, parent)
        self.assistant = StartQuitAssistant(sessionFile="LastSession.session")
        self.dbManager = DbManager(self)
        self.assistant.addSection(self.dbManager)
        self.appManager = MyAppManager(self)
        self.assistant.addSection(self.appManager)
        self.mainWindow = MyMainWindow(self)
        self.assistant.addSection(self.mainWindow)

    def start(self):
        self.assistant.start()

    def quit(self):
        self.assistant.quit()
