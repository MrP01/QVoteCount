import socket

from PySide6.QtCore import QDateTime, QProcess


class Console(object):
    class Command(object):
        def __init__(self, command):
            self.command = command

        def __call__(self, *args):
            ps = QProcess()
            ps.start(self.command, args)
            ps.waitForFinished()
            return ps.readData(4096)

    def __init__(self, cwd):
        self.cwd = cwd

    def __getattr__(self, command):
        return Console.Command(command)


class Computer(object):
    def __init__(self):
        self.name = name
        self.ip = ip


def computerName():
    return QString(socket.gethostname())


def currentDateTime():
    return QDateTime.currentDateTime()
