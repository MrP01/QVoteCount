from Engine.App import AppManager
from Engine.StartQuitAssistant import Section
from .Apps import *


class MyAppManager(AppManager, Section):
    def __init__(self, mainManager):
        AppManager.__init__(self, mainManager)
        Section.__init__(self)
        self.mainManager = mainManager

    def setupApp(self):
        app = SetupApp(self)
        self.addApp(app)
        app.start()

    def voteApp(self):
        app = VoteApp(self)
        self.addApp(app)
        app.start()

    def start(self, data):
        if len(list(self.mainManager.dbManager.db.participants.allItems())) == 0:
            self.setupApp()
        else:
            self.voteApp()
        print("Apps started")
        return True

    def quit(self):
        return bytearray()
