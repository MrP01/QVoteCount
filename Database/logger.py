from .core import (AbstractDatabaseEventFilter, AbstractContainerEventFilter)


class DbLogger(AbstractDatabaseEventFilter):
    def __init__(self, database):
        AbstractDatabaseEventFilter.__init__(self, database)
        self.isLogging = False

    def filterEvent(self, event):
        if not self.isLogging:
            return
        print("DbLog:", event)


class ContainerLogger(AbstractContainerEventFilter):
    def __init__(self, container):
        AbstractContainerEventFilter.__init__(self, container)
        self.isLogging = False
        self.logGetEvents = False

    def filterEvent(self, event):
        if not self.isLogging:
            return
        print("Log [{}]:".format(self.container.name), event)
