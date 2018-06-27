from Database.engine.sqlite import SqliteEngine
from Engine.StartQuitAssistant import Section

from .DbConfig import *


class DbManager(Section):
    def __init__(self, mainManager):
        Section.__init__(self)
        self.mainManager = mainManager
        self.db = ElectionDb(engine=SqliteEngine())
        self.keyAssignments = {}

    def start(self, sessionData):
        # try:
        # 	os.remove("election.db")
        # except FileNotFoundError:
        # 	pass
        self.db.open("election.db")
        # self.db.open("/home/peter/Schule/Sonstiges/Schulsprecherwahl/2015⁄16/election_for_new_system.db")
        # self.dbClient=self.db.createClient()
        # with self.dbClient:
        # 	self.db.participants.addItems([Participant(name="Peter"), Participant(name="Konni")])
        # 	self.db.voteGroups.addItem(VoteGroup(name="6c"))
        # self.db.votes.addItems(Vote(vote1=0, groupId=0) for i in range(100))
        print("Db started")
        return True

    def quit(self):
        import collections
        points, topVotes, voteCount, invalidVotes = self.db.calcPoints()
        sum_points = sum(points.values())
        points = collections.OrderedDict(sorted(points.items(), key=lambda i: i[1], reverse=True))
        print(30 * "-")
        print("Results [{} valid and {} invalid votes]:".format(voteCount, invalidVotes))
        for partic in points.keys():
            print("{}: {} points ({:.2f}% of total) and {} top1 votes ({:.2f}% of total)".format(
                self.db.participants.getItem(partic),
                points[partic], points[partic] / sum_points * 100,
                topVotes[partic][1], topVotes[partic][1] / voteCount * 100
            ))
        print(30 * "-")

        for partic in topVotes.keys():
            print(self.db.participants.getItem(partic))
            tv = topVotes[partic]
            for vote in tv.keys():
                print("Number of {}. votes: {}".format(vote, tv[vote]))
            print(20 * "-")

        self.db.close()
        return bytearray()
