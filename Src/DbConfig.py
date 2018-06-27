from Database.core import *


class Participant(Entity):
    name = StringAttribute("Participant name")

    def __str__(self):
        return self.name


class VoteGroup(Entity):
    name = StringAttribute("VoteGroup name")

    def __str__(self):
        return self.name


class Vote(Entity):
    vote1 = ReferenceAttribute(Participant)  # 6 Points
    vote2 = ReferenceAttribute(Participant)  # 5 Points
    vote3 = ReferenceAttribute(Participant)  # etc.
    vote4 = ReferenceAttribute(Participant)
    vote5 = ReferenceAttribute(Participant)
    vote6 = ReferenceAttribute(Participant)
    vote_group = ReferenceAttribute(VoteGroup)
    valid = BoolAttribute(True)

    def __str__(self):
        return "Vote id {}".format(self.id)


class ElectionDb(Database):
    def __init__(self, engine=None):
        Database.__init__(self, engine)
        self.participants = self.registerEntity(Participant)
        self.voteGroups = self.registerEntity(VoteGroup)
        self.votes = self.registerEntity(Vote)

    def calcPoints(self):
        points = {parti.id: 0 for parti in self.participants}
        points[-1] = 0
        # How many points each participant has (vote1: 6 points, vote2: 5 p.)
        topVotes = {parti.id: {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0} for parti in self.participants}
        topVotes[-1] = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0, 6: 0}
        # How many topVotes each participant has
        voteCount, invalidVotes = 0, 0
        maxP = min(6, len(self.participants))
        for vote in self.votes:
            if not vote.valid:
                invalidVotes += 1
                continue
            if vote.vote1:
                points[vote.vote1.id] += maxP;
                topVotes[vote.vote1.id][1] += 1
            if vote.vote2:
                points[vote.vote2.id] += maxP - 1;
                topVotes[vote.vote2.id][2] += 1
            if vote.vote3:
                points[vote.vote3.id] += maxP - 2;
                topVotes[vote.vote3.id][3] += 1
            if vote.vote4:
                points[vote.vote4.id] += maxP - 3;
                topVotes[vote.vote4.id][4] += 1
            if vote.vote5:
                points[vote.vote5.id] += maxP - 4;
                topVotes[vote.vote5.id][5] += 1
            if vote.vote6:
                points[vote.vote6.id] += maxP - 5;
                topVotes[vote.vote6.id][6] += 1
            voteCount += 1
        del points[-1], topVotes[-1]
        return points, topVotes, voteCount, invalidVotes
