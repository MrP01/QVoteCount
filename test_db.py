import os

from Database.engine.sqlite import SqliteEngine
from Src.DbConfig import *

db_path = "election_new.db"
if os.path.exists(db_path):
    os.remove(db_path)

db = ElectionDb(engine=SqliteEngine())
db.open(db_path)

with db.do():
    peter = Participant(name="Peter")
    db.participants.addItem(peter)
    konrad = Participant(name="Konrad")
    db.participants.addItem(konrad)

with db.do():
    grp = VoteGroup(name="1a")
    db.voteGroups.addItem(grp)
    vote = Vote(vote1=peter, vote2=konrad, vote_group=grp)
    print(vote.vote1, vote.vote2, vote.vote3, vote.vote_group)
    db.votes.addItem(vote)

print(list(db.participants.allItems()))

# allItems = db.votes.allItems()
# print(list(allItems))
# print(list(db.votes.engine.allItems()))
print(db.votes.getItem(1).vote_group)
print(list(db.votes.allItems()))

db.close()
