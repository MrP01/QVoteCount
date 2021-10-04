import sys

from PySide6.QtWidgets import QApplication

from Src.MainManager import MainManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    # app.setStyle(QWindowsStyle())
    manager = MainManager()
    manager.start()
    app.exec_()
