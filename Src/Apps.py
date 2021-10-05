import matplotlib, os
from PySide6.QtCore import *
from PySide6.QtWidgets import *

matplotlib.use('Qt5Agg')
# matplotlib.rcParams['backend.qt4'] = 'PySide6'

from matplotlib.figure import Figure
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from Engine.App import App
from Engine.UI import SimpleTextList, BLayoutHelper
from Engine.ContainerView import ContainerView
from Engine.QtUIWrapper import QtModelWrapper
from Engine.Message import MessagePopup

from .DbConfig import Vote, VoteGroup, Participant


class StatView(FigureCanvas):
    colors = ("#FF0000", "#00FF00", "#0000FF", "#FFFF00", "#FF00FF", "#00FFFF", "#AAAAAA", "#FFFFFF")

    # colors = ("r", "g", "b", "y")
    def __init__(self, mainManager):
        FigureCanvas.__init__(self, Figure())
        self.mainManager = mainManager

        # with self.mainManager.dbManager.dbClient:
        participants = list(self.mainManager.dbManager.db.participants.allItems())
        points, topVotes, voteCount, invalidVotes = self.mainManager.dbManager.db.calcPoints()

        # Points
        self.pointsAxes = self.figure.add_subplot(2, 1, 1)
        self.pointsAxes.set_title("Points")
        self.pointsAxes.pie(list(points.values()), explode=[0.1] * len(participants),
                            labels=[parti.name for parti in participants],
                            shadow=True, autopct="%1.1f%%", startangle=90, colors=self.colors)

        # Top1 Votes
        self.topAxes = self.figure.add_subplot(2, 1, 2)
        self.topAxes.set_title("Top1 Votes")
        self.topAxes.pie([topV[1] for pId, topV in topVotes.items()], explode=[0.1] * len(participants),
                         labels=[parti.name for parti in participants],
                         shadow=True, autopct="%1.1f%%", startangle=90, colors=self.colors)

        self.updateButton = QPushButton("Update")
        self.updateButton.clicked.connect(self.updateView)
        self._updateCount = 0

    # def sizeHint(self):
    # 	return QSize(360, 280)

    def updateView(self):
        print("UpdateView")
        # with self.mainManager.dbManager.dbClient:
        participants = list(self.mainManager.dbManager.db.participants.allItems())
        points, topVotes, voteCount, invalidVotes = self.mainManager.dbManager.db.calcPoints()
        self.pointsAxes.clear()
        self.pointsAxes.set_title("Points")
        self.pointsAxes.pie(list(points.values()), explode=[0.1] * len(participants),
                            labels=[parti.name for parti in participants],
                            shadow=True, autopct="%1.1f%%", startangle=90, colors=self.colors)
        self.topAxes.clear()
        self.topAxes.set_title("Top1 Votes")
        self.topAxes.pie([topV[1] for pId, topV in topVotes.items()], explode=[0.1] * len(participants),
                         labels=[parti.name for parti in participants],
                         shadow=True, autopct="%1.1f%%", startangle=90, colors=self.colors)
        if self._updateCount % 2 == 0:
            self.resize(self.size() + QSize(1, 1))
        else:
            self.resize(self.size() - QSize(1, 1))
        self._updateCount += 1
    # print(points, topVotes, voteCount, invalidVotes)


class KeyListener(QFrame):
    keyPressed = Signal(int)

    def __init__(self, validKeys=None, parent=None):
        QFrame.__init__(self, parent)
        self.pressedKey = None
        self.validKeys = validKeys
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Plain)
        self.setFocusPolicy(Qt.StrongFocus)
        self.label = QLabel("No focus")
        self.setLayout(BLayoutHelper(self.label))

    def keyPressEvent(self, event):
        if self.validKeys is not None and event.key() not in self.validKeys:
            event.ignore()
            return
        self.pressedKey = int(event.key())
        self.label.setText("Pressed key: {}".format(KeyListener.keyToStr(self.pressedKey)))
        self.keyPressed.emit(self.pressedKey)  # connected funcs should set label text
        event.accept()

    def clear(self):
        self.pressedKey = None
        self.label.setText("No focus")

    def focusInEvent(self, event):
        if self.pressedKey is None:
            self.label.setText("Listening...")
        event.accept()

    def focusOutEvent(self, event):
        if self.pressedKey is None:
            self.label.setText("No focus")
        event.accept()

    @staticmethod
    def keyToStr(key):
        return QKeySequence(key).toString()


class KeyAssignmentEditor(QGroupBox):
    def __init__(self, mainManager, name):
        QGroupBox.__init__(self, name)
        self.mainManger = mainManager
        self.listeners = {}
        layout = QFormLayout()
        # with self.mainManger.dbManager.dbClient:
        for participant in self.mainManger.dbManager.db.participants:
            listener = KeyListener()
            self.listeners[participant.id] = listener
            layout.addRow(participant.name, listener)
        self.setLayout(layout)

    @property
    def keyAssignments(self):
        return {listener.pressedKey: partId for partId, listener in self.listeners.items()}


class VoteEditor(QWidget):
    validKeys = list(range(Qt.Key_0, Qt.Key_9 + 1)) + list(range(Qt.Key_A, Qt.Key_Z + 1))

    def __init__(self, voteApp, parent=None):
        QWidget.__init__(self, parent)
        self.voteApp = voteApp
        self.keyListener1 = KeyListener(VoteEditor.validKeys)
        self.keyListener1.keyPressed.connect(self.keyPressed1)
        self.keyListener2 = KeyListener(VoteEditor.validKeys)
        self.keyListener2.keyPressed.connect(self.keyPressed2)
        self.keyListener3 = KeyListener(VoteEditor.validKeys)
        self.keyListener3.keyPressed.connect(self.keyPressed3)
        self.keyListener4 = KeyListener(VoteEditor.validKeys)
        self.keyListener4.keyPressed.connect(self.keyPressed4)
        self.keyListener5 = KeyListener(VoteEditor.validKeys)
        self.keyListener5.keyPressed.connect(self.keyPressed5)
        self.keyListener6 = KeyListener(VoteEditor.validKeys)
        self.keyListener6.keyPressed.connect(self.keyPressed6)
        self.addButton = QPushButton("&Vote!")
        self.invalidButton = QPushButton("Invalid vote!")
        self.addButton.clicked.connect(self.save)
        self.invalidButton.clicked.connect(self.invalidVote)
        self.groupSelector = QComboBox()
        # uiWrapper=QtModelWrapper(self.voteApp.appManager.
        # 	mainManager.dbManager.db.voteGroups)
        # uiWrapper.setModelAccessClient(self.voteApp.appManager.mainManager.dbManager.dbClient)
        # with self.voteApp.appManager.mainManager.dbManager.dbClient:
        self.groupSelector.addItems([group.name for group in self.voteApp.appManager.
                                    mainManager.dbManager.db.voteGroups])

        layout1 = QFormLayout()
        layout1.addRow("Vote 1 (6 points)", self.keyListener1)
        layout1.addRow("Vote 2 (5 points)", self.keyListener2)
        layout1.addRow("Vote 3 (4 points)", self.keyListener3)
        layout1.addRow("Group:", self.groupSelector)
        layout2 = QFormLayout()
        layout2.addRow("Vote 4 (3 points)", self.keyListener4)
        layout2.addRow("Vote 5 (2 points)", self.keyListener5)
        layout2.addRow("Vote 6 (1 points)", self.keyListener6)
        layout = QGridLayout()
        layout.addLayout(layout1, 0, 0)
        layout.addLayout(layout2, 0, 1)
        layout.addLayout(BLayoutHelper(None, self.invalidButton, self.addButton), 1, 1)
        self.setLayout(layout)

    def save(self):
        try:
            keyAssigs = self.voteApp.keyAssignmentEditor.keyAssignments
            keyAssigs[None] = -1

            def getPartic(pId):
                try:
                    return self.voteApp.appManager.mainManager.dbManager.db.participants.getItem(pId)
                except:
                    return None

            vote = Vote(vote1=getPartic(keyAssigs[self.keyListener1.pressedKey]),
                        vote2=getPartic(keyAssigs[self.keyListener2.pressedKey]),
                        vote3=getPartic(keyAssigs[self.keyListener3.pressedKey]),
                        vote4=getPartic(keyAssigs[self.keyListener4.pressedKey]),
                        vote5=getPartic(keyAssigs[self.keyListener5.pressedKey]),
                        vote6=getPartic(keyAssigs[self.keyListener6.pressedKey]),
                        vote_group=self.voteApp.appManager.mainManager.dbManager.db.voteGroups.getItem(
                            self.groupSelector.currentIndex() + 1))  # Todo
        except KeyError:  # Didn't work (key not assigned)
            MessagePopup.infoPopup(self.window(), "No key assigned",
                                   "No participant assigned to key.")
            self.clear()
            return
        if self.validate(vote):
            # with self.voteApp.appManager.mainManager.dbManager.dbClient:
            self.voteApp.appManager.mainManager.dbManager.db.votes.addItem(vote)
        else:
            MessagePopup.infoPopup(self.voteApp.appManager.mainManager.mainWindow,
                                   "Invalid vote", "A single Vote can't vote twice for a Participant.")
        self.clear()

    def clear(self):
        self.keyListener1.clear()
        self.keyListener2.clear()
        self.keyListener3.clear()
        self.keyListener4.clear()
        self.keyListener5.clear()
        self.keyListener6.clear()
        self.keyListener1.setFocus()

    def invalidVote(self):
        # with self.voteApp.appManager.mainManager.dbManager.dbClient:
        self.voteApp.appManager.mainManager.dbManager.db.votes.addItem(Vote(valid=False,
                                                                            vote_group=self.voteApp.appManager.mainManager.dbManager.db.voteGroups.getItem(
                                                                                self.groupSelector.currentIndex() + 1)))  # Todo
        self.clear()

    def validate(self, vote):
        takenVotes = []
        for partic in (vote.vote1, vote.vote2, vote.vote3, vote.vote4, vote.vote5, vote.vote6):
            if (partic is not None) and (partic in takenVotes):
                MessagePopup.infoPopup(self.voteApp.appManager.mainManager.mainWindow,
                                       "Invalid vote", "A single Vote can't vote twice for a Participant.")
                return False
            takenVotes.append(partic)
        # if (min(len(takenVotes), 6) < self.voteApp.appManager.mainManager.dbManager.db.
        # 	participants.itemCount()):
        # 	MessagePopup.infoPopup(self.voteApp.appManager.mainManager.mainWindow,
        # 		"Invalid vote", "Every participant has to be voted once.")
        # 	return False
        return True

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Return:
            self.save()
            event.accept()
            return
        event.ignore()

    def _keyPressed(self, key, keyListener, nextFocus=None):
        # with self.voteApp.appManager.mainManager.dbManager.dbClient:
        try:
            keyListener.label.setText(str(self.voteApp.appManager.mainManager.dbManager.db.
                                          participants.getItem(self.voteApp.keyAssignmentEditor.keyAssignments[key])))
        except KeyError:
            keyListener.label.setText("INVALID!")
        if nextFocus is not None:
            nextFocus.setFocus()

    keyPressed1 = lambda self, key: self._keyPressed(key, self.keyListener1, self.keyListener2)
    keyPressed2 = lambda self, key: self._keyPressed(key, self.keyListener2, self.keyListener3)
    keyPressed3 = lambda self, key: self._keyPressed(key, self.keyListener3, self.keyListener4)
    keyPressed4 = lambda self, key: self._keyPressed(key, self.keyListener4, self.keyListener5)
    keyPressed5 = lambda self, key: self._keyPressed(key, self.keyListener5, self.keyListener6)
    keyPressed6 = lambda self, key: self._keyPressed(key, self.keyListener6, self.addButton)


class VoteApp(App):
    def __init__(self, appManager):
        App.__init__(self, appManager, App.Tab, windowTitle="Vote App")
        self.uiWrapper = QtModelWrapper(self.appManager.mainManager.dbManager.db.votes)
        # self.uiWrapper.setModelAccessClient(self.appManager.mainManager.dbManager.dbClient)
        self.appManager.mainManager.dbManager.db.votes.addEventFilter(self.uiWrapper)
        self.containerView = ContainerView(self.appManager.mainManager.dbManager.db.votes, self.uiWrapper)
        self.statView = StatView(self.appManager.mainManager)
        self.keyAssignmentEditor = KeyAssignmentEditor(self.appManager.mainManager, "Assigned keys:")
        self.voteEditor = VoteEditor(self)
        self.genreportButton = QPushButton("Generate Report")
        self.genreportButton.clicked.connect(self.generateReport)
        w1 = QWidget()
        l1 = QGridLayout()
        l1.addWidget(self.keyAssignmentEditor, 0, 0)
        l1.addWidget(self.containerView, 0, 1)
        l1.addWidget(self.voteEditor, 1, 0, 1, 2)
        w1.setLayout(l1)
        w2 = QWidget()
        w2.setLayout(BLayoutHelper(self.statView, self.statView.updateButton, self.genreportButton, orientation=QBoxLayout.TopToBottom))
        splitter = QSplitter()
        splitter.addWidget(w1)
        splitter.addWidget(w2)
        self.setLayout(BLayoutHelper(splitter))

    def generateReport(self):
        report_file = os.path.abspath(self.appManager.mainManager.dbManager.generate_report())
        import webbrowser
        webbrowser.open("file://" + report_file)


class SetupApp(App):
    def __init__(self, appManager):
        App.__init__(self, appManager, windowTitle="Setup Election")
        # with self.appManager.mainManager.dbManager.dbClient:
        self.participantList = SimpleTextList("Participants", items=(parti.name for parti in
                                                                     self.appManager.mainManager.dbManager.db.participants.allItems()))
        self.groupList = SimpleTextList("Groups", items=(group.name for group in
                                                         self.appManager.mainManager.dbManager.db.voteGroups.allItems()))
        self.submitButton = QPushButton("Submit")
        layout = QVBoxLayout()
        layout.addWidget(self.participantList)
        layout.addWidget(self.groupList)
        layout.addLayout(BLayoutHelper(None, self.submitButton))
        self.setLayout(layout)
        self.submitButton.clicked.connect(self.submit)

    def submit(self):
        # with self.appManager.mainManager.dbManager.dbClient:
        # partic_before = set([p.name for p in self.appManager.mainManager.dbManager.db.participants.allItems()])
        # partic_after = set(self.participantList.allItems())
        # diff = partic_before.difference(partic_after)
        # if diff:
        #     self.appManager.mainManager.dbManager.db.participants.addItems()
        self.appManager.mainManager.dbManager.db.participants.clear()
        self.appManager.mainManager.dbManager.db.participants.addItems(
            Participant(name=name) for name in self.participantList.allItems())
        self.appManager.mainManager.dbManager.db.voteGroups.clear()
        self.appManager.mainManager.dbManager.db.voteGroups.addItems(
            VoteGroup(name=item) for item in self.groupList.allItems())
        self.quit()
        self.appManager.voteApp()
