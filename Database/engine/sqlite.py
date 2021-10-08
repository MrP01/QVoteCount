import collections
import os
import sqlite3.dbapi2 as sqlite3
import threading

from .. import core, tools


class ContainerEngine(core.AbstractContainerEngine):
    attrTypes = {
        core.IntAttribute: "INTEGER",
        core.StringAttribute: "TEXT",
        core.DateTimeAttribute: "TIMESTAMP",
        core.BoolAttribute: "INTEGER",
        core.FloatAttribute: "REAL",
        core.BlobAttribute: "BLOB",
    }

    def __init__(self, container):
        core.AbstractContainerEngine.__init__(self, container)
        self._cursors = collections.defaultdict(self._createCursor)
        self.entityCls = self.container.entityCls
        self.colNames = self.entityCls.attributes.keys()
        self._createSql()

    def addItem(self, item):
        self.cursor.execute(self._addSql, self._makeVals(item))
        return self.cursor.lastrowid

    def addItems(self, items):
        items = iter(items)
        self.cursor.execute(self._addSql, self._makeVals(next(items)))
        idStart = self.cursor.lastrowid
        l = [1]

        def fun(item): l[0] += 1; return self._makeVals(item)

        self.cursor.executemany(self._addSql, map(fun, items))
        return range(idStart, idStart + l[0])

    def getItem(self, itemId):
        self.cursor.execute(self._getSql, (itemId,))
        row = self.cursor.fetchone()
        if row is None:
            raise core.ItemError(itemId, core.ItemError.notExistingTxt)
        return self._makeItem(row)

    def getItems(self, itemIds):
        for itemId in itemIds:
            yield self.getItem(itemId)

    def insertItem(self, item):
        try:
            self.cursor.execute(self._insertSql, self._makeVals(item))
        except sqlite3.IntegrityError:
            raise core.ItemError(item.id, core.ItemError.alreadyExistingTxt)

    def _checkItemsNotExistGen(self, items):
        for item in items:
            self._assertNotExists(item.id)
            yield self._makeVals(item)

    def insertItems(self, items):
        self.cursor.executemany(self._insertSql, self._checkItemsNotExistGen(items))

    def setItem(self, item):
        self._assertExists(item.id)
        self.cursor.execute(self._setSql, self._makeVals(item))

    def _checkItemsExistGen(self, items):
        for item in items:
            self._assertExists(item.id)
            yield self._makeVals(item)

    def setItems(self, items):
        self.cursor.executemany(self._setSql, self._checkItemsExistGen(items))

    def removeItem(self, itemId):
        self._assertExists(itemId)
        self.cursor.execute(self._removeSql, (itemId,))

    def _checkIdsExistGen(self, itemIds):
        for itemId in itemIds:
            self._assertExists(itemId)
            yield itemId

    def removeItems(self, itemIds):
        self.cursor.executemany(self._removeSql, self._checkIdsExistGen(itemIds))

    def filterItems(self, check):
        return filter(check, self.allItems())

    def itemIds(self):
        self.cursor.execute(self._getIdsSql)
        for row in iter(self.cursor.fetchone, None):
            yield row[0]

    def allItems(self):
        cursor = self.cursor  # So the cursor-property getter doesn't get called so often
        cursor.execute(self._getAllSql)
        return map(self._makeItem, iter(self.cursor.fetchone, None))

    def clear(self):
        self.cursor.execute(self._clearSql)

    def itemCount(self):
        self.cursor.execute(self._countSql)
        return self.cursor.fetchone()[0]

    def checkItemExists(self, itemId):
        self.cursor.execute(self._checkItemSql, (itemId,))
        return self.cursor.fetchone() is not None

    def createTableSchema(self):
        fields = []
        for name, attr in self.entityCls.attributes.items():
            if name == "id":
                fields.append("id INTEGER PRIMARY KEY")  # doesn't use rowid/oid for clarity purposes
                continue
            fields.append(r"{name} {type} DEFAULT '{default}'".format(name=name,
                                                                      type=ContainerEngine.fieldType(attr),
                                                                      default=attr.intern_default))
        return "CREATE TABLE IF NOT EXISTS {tblName} ({fields});".format(
            tblName=self.tblName, fields=", ".join(fields))

    def _createSql(self):
        """pre-defines all sql statements, so it works faster"""
        # same as insertSql but without assigning an id
        self._addSql = "INSERT INTO {tblName} ({fields}) VALUES ({values});" \
            .format(tblName=self.tblName, fields=", ".join(name for name in self.colNames if name != "id"),
                    values=", ".join(":" + name for name in self.colNames if name != "id"))
        self._insertSql = "INSERT INTO {tblName} ({fields}) VALUES ({values});" \
            .format(tblName=self.tblName, fields=", ".join(self.colNames),
                    values=", ".join(":" + name for name in self.colNames))
        self._setSql = "UPDATE {tblName} SET {fields} WHERE id=:id;" \
            .format(tblName=self.tblName, fields=", ".join("{name}=:{name}".format(name=name)
                                                           for name in self.colNames if name != "id"))
        self._getSql = "SELECT * FROM {tblName} WHERE id=?;" \
            .format(tblName=self.tblName)
        self._getManySql = "SELECT * FROM {tblName} WHERE id in (?);" \
            .format(tblName=self.tblName)
        self._getAllSql = "SELECT * FROM {tblName};" \
            .format(tblName=self.tblName)
        self._getIdsSql = "SELECT id FROM {tblName};" \
            .format(tblName=self.tblName)
        self._checkItemSql = "SELECT id FROM {tblName} WHERE id=? LIMIT 1;" \
            .format(tblName=self.tblName)
        self._countSql = "SELECT COUNT (*) FROM {tblName};" \
            .format(tblName=self.tblName)
        self._removeSql = "DELETE FROM {tblName} WHERE id=?;" \
            .format(tblName=self.tblName)
        # noinspection SqlWithoutWhere
        self._clearSql = "DELETE FROM {tblName};" \
            .format(tblName=self.tblName)

    def _makeVals(self, item):
        return {name: getattr(item, name) for name in self.colNames}

    def _makeItem(self, data):
        return self.entityCls(**dict(zip(self.colNames, data)))

    def _assertExists(self, itemId):
        if not self.checkItemExists(itemId):
            raise core.ItemError(itemId, core.ItemError.notExistingTxt)

    def _assertNotExists(self, itemId):
        if self.checkItemExists(itemId):
            raise core.ItemError(itemId, core.ItemError.alreadyExistingTxt)

    @staticmethod
    def fieldType(attr):
        tp = tools.isinstancePool(attr, ContainerEngine.attrTypes)
        if tp is None:
            raise NotImplementedError("That type is not implemented in SqliteEngine: {}".format(type(attr)))
        return tp

    @property
    def cursor(self):
        """Returns a sqlite3.Cursor for this table

        Returns a cursor object for this thread;
        if necessary, a new one is created
        """
        return self._cursors[threading.get_ident()]

    def _createCursor(self):
        return self.mainEngine.connection.cursor()

    tblName = property(lambda self: self.entityCls.__realName__)


# entityCls=property(lambda self: self.container.entityCls) #too slow


class SqliteEngine(core.AbstractDatabaseEngine):
    """Implements sqlite3 support"""

    def __init__(self):
        """Initializes a new Engine object"""
        core.AbstractDatabaseEngine.__init__(self)
        self._connections = collections.defaultdict(self._createConn)
        self._path = ""

    def commit(self):
        self.connection.commit()

    def checkAccess(self):
        pass

    def createContainerEngine(self, container):
        return ContainerEngine(container)

    def open(self, path):
        self._path = path
        new = not os.path.exists(self._path)
        self._createConn()
        if new:
            sql = "".join(cont.engine.createTableSchema()
                          for cont in self.database.containers.values())
            print("EXEC SQL:", sql)
            self.connection.executescript(sql)
            self.commit()
        return new

    def close(self):
        self.commit()
        self.connection.close()

    @property
    def connection(self):  # "Public" attribute, so it is possible to execute sql-statements from outside
        """Returns a sqlite3.Connection object

         Returns the connection object for the current thread;
         if necessary, a new one is created
         """
        return self._connections[threading.get_ident()]

    def _createConn(self):
        return sqlite3.connect(self._path, detect_types=sqlite3.PARSE_DECLTYPES)
