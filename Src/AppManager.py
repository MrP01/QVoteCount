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

    def voteApp(self, *args, **kwargs):
        app = VoteApp(self, *args, **kwargs)
        self.addApp(app)
        app.start()

    def start(self, data):
        self.setupApp()
        print("Apps started")
        return True

    def quit(self):
        return bytearray()
