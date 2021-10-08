import jinja2

from Database.engine.sqlite import SqliteEngine
from Engine.StartQuitAssistant import Section
from .DbConfig import *


class DbManager(Section):
    def __init__(self, mainManager):
        Section.__init__(self)
        self.mainManager = mainManager
        self.db = ElectionDb(engine=SqliteEngine())
        self.keyAssignments = {}

    def generate_report(self):
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

        env = jinja2.Environment()
        template = env.get_template("report.jinja")
        today = datetime.date.today()
        report_file = "Bericht Schulsprecherwahl %s.html" % today.year
        with open(report_file, "w") as f:
            f.write(template.render(
                today=today,
                sum_points=sum_points,
                valid_votes=voteCount,
                invalid_votes=invalidVotes,
                participants=[{
                    "name": self.db.participants.getItem(partic_id),
                    "points": pts,
                    "points_perc": pts / sum_points * 100,
                    "top_votes": topVotes[partic_id],
                    "top_votes_perc": topVotes[partic_id],
                } for partic_id, pts in points.items()]
            ))
        return report_file

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
        self.db.close()
        return bytearray()
