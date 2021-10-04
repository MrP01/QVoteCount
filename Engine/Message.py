from PySide6.QtCore import QSize, QTimer, Qt
from PySide6.QtWidgets import (QLabel, QHBoxLayout, QVBoxLayout, QIcon, QPainter,
                          QColor, QPushButton)

from .MainWindow import PopupDialog


class MessagePopup(PopupDialog):
    Info = 0
    Warning = 1

    def __init__(self, mainWindow, delete=True):
        PopupDialog.__init__(self, mainWindow)
        self._type = MessagePopup.Info
        self._color = QColor()
        self._delete = delete
        self.initUI()

    def initUI(self):
        self.iconLabel = QLabel()
        self.titleLabel = QLabel("Title")
        self.textLabel = QLabel("Text")
        self.textLabel.setWordWrap(True)
        # ~ self.textLabel.setFixedWidth(200)

        layout = QHBoxLayout()
        layout.addWidget(self.iconLabel)
        titleTextLayout = QVBoxLayout()
        titleTextLayout.addWidget(self.titleLabel)
        textLayout = QHBoxLayout()
        textLayout.addSpacing(10)
        textLayout.addWidget(self.textLabel)
        titleTextLayout.addLayout(textLayout)
        titleTextLayout.addStretch()
        layout.addLayout(titleTextLayout)
        self.setLayout(layout)

        self.infoIcon = QIcon.fromTheme("dialog-information")
        self.questionIcon = QIcon.fromTheme("dialog-question")
        self.warningIcon = QIcon.fromTheme("dialog-warning")
        self.errorIcon = QIcon.fromTheme("dialog-error")

    def info(self, title, text, timeout=3000, color=QColor(170, 220, 230)):
        self._type = MessagePopup.Info
        self._color = color
        self.iconLabel.setPixmap(self.infoIcon.pixmap(QSize(64, 64)))
        self.titleLabel.setText("<b>%s</b>" % title)
        self.textLabel.setText("%s" % text)
        self.popup()
        if timeout >= 0:
            QTimer.singleShot(timeout, self.cancel)

    def warning(self, title, text, timeout=3000, color=QColor(215, 130, 140)):
        self._type = MessagePopup.Warning
        self._color = color
        self.iconLabel.setPixmap(self.warningIcon.pixmap(QSize(64, 64)))
        self.titleLabel.setText("<b>%s</b>" % title)
        self.textLabel.setText(text)
        self.popup()
        if timeout >= 0:
            QTimer.singleShot(timeout, self.cancel)

    def cancel(self):
        PopupDialog.cancel(self)
        if self._delete:
            self.deleteLater()

    def focusOutEvent(self, event):
        self.cancel()
        event.accept()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.hide()
            event.accept()
            return
        PopupDialog.keyPressEvent(self, event)

    def mouseReleaseEvent(self, event):
        self.reject()
        event.accept()

    def paintBackground(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self._color)
        self.drawFrame(painter)

    @staticmethod
    def infoPopup(mainWin, title, txt, timeout=3000, color=QColor(170, 220, 230)):
        popup = MessagePopup(mainWin)
        popup.info(title, txt, timeout, color)
        return popup

    @staticmethod
    def warningPopup(mainWin, title, txt, timeout=3000, color=QColor(215, 130, 140)):
        popup = MessagePopup(mainWin)
        popup.warning(title, txt, timeout, color)
        return popup


class ProblemPopup(PopupDialog):
    Info = 0
    Warning = 1

    def __init__(self, mainWindow, delete=True):
        PopupDialog.__init__(self, mainWindow)
        self._type = MessagePopup.Info
        self._delete = delete
        self.initUI()

    def initUI(self):
        self.iconLabel = QLabel()
        self.titleLabel = QLabel("Title")
        self.textLabel = QLabel("Text")
        self.textLabel.setWordWrap(True)
        # ~ self.textLabel.setFixedWidth(200)
        self.retryButton = QPushButton("&Retry")
        self.cancelButton = QPushButton("&Cancel")

        layout = QHBoxLayout()
        layout.addWidget(self.iconLabel)
        titleTextLayout = QVBoxLayout()
        titleTextLayout.addWidget(self.titleLabel)
        textLayout = QHBoxLayout()
        textLayout.addSpacing(10)
        textLayout.addWidget(self.textLabel)
        titleTextLayout.addLayout(textLayout)
        titleTextLayout.addStretch()
        buttonLayout = QHBoxLayout()
        buttonLayout.addWidget(self.retryButton)
        buttonLayout.addWidget(self.cancelButton)
        titleTextLayout.addLayout(buttonLayout)
        layout.addLayout(titleTextLayout)
        self.setLayout(layout)

        self.retryButton.clicked.connect(self.accept)
        self.cancelButton.clicked.connect(self.reject)

        self.infoIcon = QIcon.fromTheme("dialog-information")
        self.questionIcon = QIcon.fromTheme("dialog-question")
        self.warningIcon = QIcon.fromTheme("dialog-warning")
        self.errorIcon = QIcon.fromTheme("dialog-error")

    def info(self, title, text, timeout=3000):
        self._type = MessagePopup.Info
        self.iconLabel.setPixmap(self.infoIcon.pixmap(QSize(64, 64)))
        self.titleLabel.setText("<b>%s</b>" % title)
        self.textLabel.setText("%s" % text)
        self.popup()

    def warning(self, title, text, timeout=3000):
        self._type = MessagePopup.Warning
        self.iconLabel.setPixmap(self.warningIcon.pixmap(QSize(64, 64)))
        self.titleLabel.setText("<b>%s</b>" % title)
        self.textLabel.setText(text)
        self.popup()

    def cancel(self):
        PopupDialog.cancel(self)
        if self._delete:
            self.deleteLater()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.hide()
            event.accept();
            return
        PopupDialog.keyPressEvent(self, event)

    def paintBackground(self):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        if self._type == MessagePopup.Info:
            painter.fillRect(self.rect(), QColor(170, 220, 230))
        elif self._type == MessagePopup.Warning:
            painter.fillRect(self.rect(), QColor(230, 60, 60))
        self.drawFrame(painter)
