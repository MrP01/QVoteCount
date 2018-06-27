import struct

from PySide.QtCore import QObject, Signal

from Database.datastream import DataStream


class NotStartedError(Exception):
    pass


class Section(object):
    def start(self, sessionData):
        return True

    def quit(self):
        return bytearray()


class SectionControl(object):
    def __init__(self, section):
        self.section = section
        self.data = bytearray()
        self.started = False

    def start(self):
        self.started = self.section.start(self.data)
        return self.started

    def quit(self):
        self.data = self.section.quit()
        self.started = False


class StartQuitAssistant(QObject):
    sectionStarted = Signal()
    sectionFailed = Signal()
    started = Signal()
    quitted = Signal()

    def __init__(self, sections=None, sessionFile=None, parent=None):
        QObject.__init__(self, parent)
        if sections is None:
            sections = []
        self._sections = sections
        self._started = False
        self._sessionFile = None
        if sessionFile is not None:
            self.sessionFile = sessionFile

    def addSection(self, section):
        self._sections.append(SectionControl(section))

    def start(self):
        self.loadSession()
        for meta in self._sections:
            if meta.start():
                self.sectionStarted.emit()
            else:
                self.sectionFailed.emit()
                self.abortStart()
                return False
        self._started = True
        self.started.emit()
        return True

    def quit(self):
        if not self._started:
            raise NotStartedError()
        for section in reversed(self._sections):
            section.quit()
        self.saveSession()
        self.quitted.emit()

    def abortStart(self):
        for section in reversed(self._sections):
            if section.started:
                section.quit()
        self.saveSession()
        self.quitted.emit()

    def loadSession(self):
        if self.sessionFile is None:
            return
        try:
            with open(self.sessionFile, "rb") as file:
                stream = DataStream(file.read())
        except FileNotFoundError:
            return
        try:
            for meta in self._sections:
                meta.data = stream.readBlob()
        except struct.error:
            print("Could not load file")

    def saveSession(self):
        if self.sessionFile is None:
            return
        data = bytearray()
        stream = DataStream(data)
        for meta in self._sections:
            stream.writeBlob(meta.data)
        with open(self.sessionFile, "wb") as file:
            file.write(data)

    def sessionFile(self):
        return self._sessionFile

    def setSessionFile(self, file):
        self._sessionFile = file

    sessionFile = property(sessionFile, setSessionFile)
