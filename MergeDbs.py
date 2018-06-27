from Database.sqliteEngine import SqliteEngine

from Src.DbConfig import *

db1 = ElectionDb(engine=SqliteEngine())
db2 = ElectionDb(engine=SqliteEngine())

db1.open(filePath="election.db")
