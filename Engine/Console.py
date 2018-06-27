from PySide.QtCore import Qt
from PySide.QtGui import QFont


def coloredPrint(text, color=Qt.black, highlight=None, font=QFont()):
    args = str()
    if font.bold():
        args += "1;"
    if font.italic():
        args += "3;"
    if font.underline():
        args += "4;"
    args = args[:-1]
    print("\033[" + args + "m" + text + "\033[1;m")


coloredPrint("Hallo2")
