import psycopg2

from ..core import (AbstractDatabaseEngine, AbstractContainerEngine, ItemError,
                    MetaItem, BoolAttribute, DateTimeAttribute, StringAttribute, IntAttribute,
                    FloatAttribute, BlobAttribute)
from ..tools import isinstancePool


class PgSqlTable(object):
    attrTypes = {
        IntAttribute: "INTEGER",
        StringAttribute: "TEXT",
        DateTimeAttribute: "TIMESTAMP",
        BoolAttribute: "BOOLEAN",
        FloatAttribute: "REAL",
        BlobAttribute: "BLOB",
    }

    def __init__(self, tblName, entityCls, connection=None):
        # Define sql statements to effectively increase speed
        self.tblName = tblName
        self.entityCls = entityCls
        self._insertSql = "INSERT INTO {tblName} ({fields}) VALUES ({values});" \
            .format(tblName=self.tblName, fields=", ".join(self.entityCls.attributes.keys()),
                    values=", ".join(":" + name for name in self.entityCls.attributes.keys()))
        self._setSql = "UPDATE {tblName} SET {fields} WHERE id=:id;" \
            .format(tblName=self.tblName, fields=", ".join("{name}=:{name}".format(name=name)
                                                           for name in self.entityCls.attributes.keys() if
                                                           name != "id"))
        self._getSql = "SELECT * FROM {tblName} WHERE id=?;" \
            .format(tblName=self.tblName)
        self._getManySql = "SELECT * FROM {tblName} WHERE id in (?);" \
            .format(tblName=tblName)
        self._getAllSql = "SELECT * FROM {tblName};" \
            .format(tblName=self.tblName)
        self._getIdsSql = "SELECT id FROM {tblName};" \
            .format(tblName=self.tblName)
        self._checkItemSql = "SELECT id FROM {tblName} WHERE id=? LIMIT 1;" \
            .format(tblName=tblName)
        self._countSql = "SELECT COUNT (*) FROM {tblName};" \
            .format(tblName=self.tblName)
        self._removeSql = "DELETE FROM {tblName} WHERE id=?;" \
            .format(tblName=self.tblName)
        self._clearSql = "DELETE FROM {tblName};" \
            .format(tblName=self.tblName)
        self._connection = None
        self.cursor = None
        if connection is not None:
            self.connection = connection

    # if self.connection is None:
    # 	self.connection=psycopg2.connect(":memory:", detect_types=psycopg2.PARSE_DECLTYPES)
    # if self.cursor is None:
    # 	self.cursor=self.connection.cursor()

    def createTableSchema(self):
        if "id" not in self.entityCls.attributes.keys():
            raise RuntimeError("PgSqlTable only accepts item WITH an id (i.e. primary Key)")
        fields = []
        for name, attr in self.entityCls.attributes.items():
            if name == "id":
                fields.append("id INT PRIMARY KEY")
                continue
            fields.append(r"{name} {type} DEFAULT '{default}'".format(name=name,
                                                                      type=PgSqlTable.fieldType(attr),
                                                                      default=attr.default))
        return "CREATE TABLE {tblName} ({fields});".format(
            tblName=self.tblName, fields=", ".join(fields))

    def createTable(self, exists_ok=False):
        try:
            self.cursor.execute(self.createTableSchema())
        except psycopg2.OperationalError:
            if not exists_ok:
                raise

    @staticmethod
    def fieldType(attr):
        tp = isinstancePool(attr, PgSqlTable.attrTypes)
        if tp is None:
            raise NotImplementedError("That type is not implemented in SqliteEngine: {}".format(type(attr)))
        return tp

    def addItem(self, item):
        item.id = self.nextItemId()
        self.cursor.execute(self._insertSql, {name: getattr(item, name)
                                              for name in self.entityCls.attributes.keys()})
        return item.id

    def _assignIdsGen(self, items):
        itemId = self.nextItemId()
        for item in items:
            item.id = itemId
            yield {name: getattr(item, name)
                   for name in self.entityCls.attributes.keys()}
            itemId += 1

    def addItems(self, items):
        # if len(items) > 1000:
        # 	raise ValueError("PgSql cannot add more than 1000 items (items: {})".format(len(items))) #Todo
        self.cursor.executemany(self._insertSql, self._assignIdsGen(items))
        return (item.id for item in items)

    def insertItem(self, item):
        try:
            self.cursor.execute(self._insertSql,
                                {name: getattr(item, name) for name in self.entityCls.attributes.keys()})
        except psycopg2.IntegrityError:
            raise ItemError(item.id) from None

    def _checkItemsNotExistGen(self, items):
        for item in items:
            if self.checkItemExists(item.id):
                raise ItemError(item.id)
            yield {name: getattr(item, name)
                   for name in self.entityCls.attributes.keys()}

    def insertItems(self, items):
        self.cursor.executemany(self._insertSql, self._checkItemsNotExistGen(items))

    def getItem(self, itemId):
        self.cursor.execute(self._getSql, (itemId,))
        fetchedData = self.cursor.fetchone()
        if fetchedData is None:
            raise ItemError(itemId)
        return self.entityCls(**dict(zip(self.entityCls.attributes.keys(), fetchedData)))

    def getItems(self, itemIds):
        self.cursor.execute(self._getManySql, ",".join(itemIds))
        row = self.cursor.fetchone()
        while row:
            yield self.entityCls(**dict(zip(self.entityCls.attributes.keys(), row)))
            row = self.cursor.fetchone()

    def setItem(self, item):
        if not self.checkItemExists(item.id):
            raise ItemError(item.id)
        self.cursor.execute(self._setSql, {name: getattr(item, name)
                                           for name in self.entityCls.attributes.keys()})

    def _checkItemsExistGen(self, items):
        for item in items:
            if not self.checkItemExists(item.id):
                raise ItemError(item.id)
            yield {name: getattr(item, name)
                   for name in self.entityCls.attributes.keys()}

    def setItems(self, items):
        self.cursor.executemany(self._setSql, self._checkItemsExistGen(items))

    def removeItem(self, itemId):
        if not self.checkItemExists(itemId):
            raise ItemError(itemId)
        self.cursor.execute(self._removeSql, itemId)

    def _checkIdsExistGen(self, itemIds):
        for itemId in itemIds:
            if not self.checkItemExists(itemId):
                raise ItemError(itemId)
            yield itemId

    def removeItems(self, itemIds):
        self.cursor.executemany(self._removeSql, self._checkIdsExistGen(itemIds))

    def filter(self, check):
        return filter(check, self.allItems())

    def allItems(self):
        self.cursor.execute(self._getAllSql)
        row = self.cursor.fetchone()
        while row:
            yield self.entityCls(**dict(zip(self.entityCls.attributes.keys(), row)))
            row = self.cursor.fetchone()

    def itemIds(self):
        self.cursor.execute(self._getIdsSql)
        return (row[0] for row in self.cursor.fetchall())

    def clear(self):
        self.cursor.execute(self._clearSql)

    def itemCount(self):
        self.cursor.execute(self._countSql)
        return self.cursor.fetchone()[0]

    def checkItemExists(self, itemId):
        self.cursor.execute(self._checkItemSql, (itemId,))
        return self.cursor.fetchone() is not None

    def nextItemId(self):
        try:
            return max(self.itemIds()) + 1
        except ValueError:
            return 0

    def connection(self):
        return self._connection

    def setConnection(self, connection):
        self._connection = connection
        self.cursor = self.connection.cursor()

    connection = property(connection, setConnection)


class ContainerEngine(PgSqlTable, AbstractContainerEngine):
    def __init__(self, container):
        AbstractContainerEngine.__init__(self, container)
        PgSqlTable.__init__(self, container.realName, container.entityCls)
        self._metas = PgSqlTable("{}_meta".format(container.realName), MetaItem)

    def configConnection(self):
        self.connection = self.mainEngine.connection
        self._metas.connection = self.connection

    def createTableSchema(self):
        return PgSqlTable.createTableSchema(self) + self._metas.createTableSchema()

    def addItem(self, item):
        item.id = PgSqlTable.addItem(self, item)
        self._metas.insertItem(MetaItem(id=item.id,
                                        lastUpdate=self.container.database.currentDateTime()))
        return item.id

    def _insertOrSetMetasGen(self, items, lastUpdate, deleted):
        for item in items:
            yield item
            try:
                self._metas.insertItem(MetaItem(id=item.id, lastUpdate=lastUpdate,
                                                deleted=deleted))
            except ItemError:
                self._metas.setItem(MetaItem(id=item.id, lastUpdate=lastUpdate,
                                             deleted=deleted))

    def addItems(self, items):
        return PgSqlTable.addItems(self, self._insertOrSetMetasGen(items,
                                                                   self.container.database.currentDateTime(), False))

    def insertItem(self, item):
        PgSqlTable.insertItem(self, item)
        try:
            self._metas.insertItem(MetaItem(id=item.id,
                                            lastUpdate=self.container.database.currentDateTime()))
        except ItemError:
            self._metas.setItem(MetaItem(id=item.id,
                                         lastUpdate=self.container.database.currentDateTime()))

    def insertItems(self, items):
        PgSqlTable.insertItems(self, self._insertOrSetMetasGen(items,
                                                               self.container.database.currentDateTime(), False))

    def setItem(self, item):
        PgSqlTable.setItem(self, item)
        self._metas.setItem(MetaItem(id=item.id,
                                     lastUpdate=self.container.database.currentDateTime()))

    def setItems(self, items):
        PgSqlTable.setItems(self, self._insertOrSetMetasGen(items,
                                                            self.container.database.currentDateTime(), False))

    def removeItem(self, itemId):
        PgSqlTable.removeItem(self, itemId)
        self._metas.setItem(MetaItem(id=itemId,
                                     lastUpdate=self.container.database.currentDateTime(),
                                     deleted=True))

    def _setMetasDeletedGen(self, itemIds, lastUpdate):
        for itemId in itemIds:
            yield itemId
            self._metas.setItem(MetaItem(id=itemId, lastUpdate=lastUpdate,
                                         deleted=True))

    def removeItems(self, itemIds):
        PgSqlTable.removeItems(self, self._setMetasDeletedGen(itemIds,
                                                              self.container.database.currentDateTime()))

    def update(self):
        pass

    def metaItem(self, itemId):
        return self._metas.getItem(itemId)

    def metaItems(self):
        return self._metas.allItems()

    def filterItems(self, check):
        print("Filter now")
        return filter(check, self.allItems())

    # def allItems(self):
    # 	return PgSqlTable.allItems(self)
    #
    # def itemIds(self):
    # 	return PgSqlTable.itemIds(self)

    def clear(self):
        PgSqlTable.clear(self)
        self._metas.clear()

    # def itemCount(self):
    # 	return PgSqlTable.itemCount(self)

    def nextItemId(self):
        try:
            return max(self._metas.itemIds()) + 1
        except ValueError:
            return 0


class PgSqlEngine(AbstractDatabaseEngine):
    def __init__(self):
        AbstractDatabaseEngine.__init__(self)
        self._connection = None

    # self._host, self._port, self._user, self._password,\
    # 	self._dbName="", "", "", "", ""

    def open(self, dbName="", host="", port=5432, user="", password=""):
        new = False
        while True:
            try:
                self._connection = psycopg2.connect(database=dbName, host=host, port=port,
                                                    user=user, password=password)
                break
            except psycopg2.OperationalError as e:
                print("Db not exist:", e)
                new = True
                conn = psycopg2.connect(database="postgres", host=host, port=port,
                                        user=user, password=password)
                conn.set_isolation_level(psycopg2.extensions.ISOLATION_LEVEL_AUTOCOMMIT)
                conn.cursor().execute("CREATE DATABASE %s;" % dbName)  # WARNING, security issue
                conn.close()
        for container in self.database.containers.values():
            container.engine.configConnection()
        if new:
            self.connection.cursor().execute(self.createSchema())
        return new

    def close(self):
        self.commit()
        self.connection.close()

    def commit(self):
        self.connection.commit()

    def checkAccess(self):
        return True

    def createContainerEngine(self, container):
        return ContainerEngine(container)

    def createSchema(self):
        sql = ""
        for container in self.database.containers.values():
            container.engine.createTableSchema()
        return sql

    @property
    def connection(self):
        return self._connection
