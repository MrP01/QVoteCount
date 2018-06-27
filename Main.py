import sys

from PySide.QtGui import *

from Src.MainManager import MainManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle(QWindowsStyle())
    manager = MainManager()
    manager.start()
    app.exec_()
