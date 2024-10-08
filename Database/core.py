import collections
import contextlib
import datetime
import functools
import re
from abc import ABCMeta, abstractmethod


# Exceptions


class DatabaseError(Exception):  # Base Class for DB Errors
    pass


class AccessError(DatabaseError):
    pass


class ItemError(DatabaseError):  # (i.e. KeyError) must be subclass of DatabaseError
    notExistingTxt = "Item does not exist"
    alreadyExistingTxt = "Item does already exist"

    def __init__(self, itemId, msg=None):
        DatabaseError.__init__(self)
        self.itemId = itemId
        self.msg = msg

    def __str__(self):
        return "ItemId {itemId}: {msg}".format(itemId=self.itemId, msg=self.msg)


# Attributes


# noinspection PyMethodMayBeStatic
class Attribute(object, metaclass=ABCMeta):
    def __init__(self, default):
        self.default = default
        self.intern_default = default

    def reprValue(self, value):
        return str(value)

    def lessThan(self, v1, v2):  # v1 less than v2 -> True
        return v1 < v2


class IntAttribute(Attribute):
    Int8, Int16, Int32, Int64 = range(4)

    def __init__(self, default, size=Int16):
        Attribute.__init__(self, default)
        self.size = size


class IdAttribute(IntAttribute):  # Id
    def __init__(self):
        IntAttribute.__init__(self, -1, IntAttribute.Int32)


class BoolAttribute(Attribute):
    pass


class FloatAttribute(Attribute):
    Single, Double = range(2)

    def __init__(self, default, size=Single):
        Attribute.__init__(self, default)
        self.size = size


class StringAttribute(Attribute):
    pass


class BlobAttribute(Attribute):
    pass


class DateTimeAttribute(Attribute):
    pass


class ReferenceAttribute(IdAttribute):
    def __init__(self, entityCls):
        IdAttribute.__init__(self)
        self.entityCls = entityCls  # The entity it references
        self.default = None
        self.intern_default = -1


# class ListAttribute(BlobAttribute):
# 	def __init__(self, itemsType, default):
# 		BlobAttribute.__init__(self, None)
# 		self.itemsType=itemsType
# 		self.default=
# 	def write(self, device, value):
# 		DataStream.writeUInt16(device, len(value))
# 		for item in value:
# 			self.itemsType.write(device, item)
# 	def read(self, device):
# 		value=[]
# 		itemCount=DataStream.readUInt16(device)
# 		for i in range(itemCount):
# 			value.append(self.itemsType.read(device))
# 		return value


# Entity API


class EntityMeta(type):
    def __new__(mcs, name, bases, attrs):
        attributes = {}  # unsorted
        for base in reversed(bases):  # Reversed, so the base on the left has the final say
            if isinstance(base, mcs):
                attributes.update(base.attributes)
        attrs_ = attrs.copy()
        for name_, value in attrs.items():
            if isinstance(value, Attribute):
                attributes[name_] = value
                del attrs_[name_]  # So the "class variables" (=static vars) don't conflict with the Attributes
        attrs_["attributes"] = collections.OrderedDict()
        attrs_["attributes"].update(sorted(attributes.items(), key=lambda item: item[0]))
        attrs_["__slots__"] = tuple(attributes.keys())
        if "__realName__" not in attrs_:
            attrs_["__realName__"] = name.lower() + "s"
        if not re.fullmatch(r"\w+", attrs_["__realName__"]):
            raise NameError("Name may only contain characters A-Z, a-z, 0-9 and '_'")
        if "__containerName__" not in attrs_:
            attrs_["__containerName__"] = attrs_["__realName__"]
        return type.__new__(mcs, name, bases, attrs_)

    def __getattribute__(self, item):
        if item in type.__getattribute__(self, "attributes").keys():
            return type.__getattribute__(self, "attributes")[item]
        return type.__getattribute__(self, item)


class AbstractEntity(object, metaclass=EntityMeta):
    __slots__ = ()
    attributes = {}

    def __init__(self, **kwargs):
        if len(kwargs) > len(self.__class__.attributes):
            raise AttributeError("Too many arguments")
        for name, attr in self.__class__.attributes.items():
            if name in kwargs.keys():
                setattr(self, name, kwargs[name])
                del kwargs[name]
                continue
            setattr(self, name, attr.default)
        if kwargs:
            raise AttributeError("No such arguments: {}".format(tuple(kwargs.keys())))
        self.validate()

    def validate(self):
        # throw exceptions
        pass

    @classmethod
    def writeItem(cls, device, item):
        for name, field in cls.attributes.items():
            field.write(device, getattr(item, name))

    @classmethod
    def readItem(cls, device):
        item = cls()
        for name, field in cls.attributes.items():
            setattr(item, name, field.read(device))
        return item

    def copy(self, **kwargs):
        kws = {name: getattr(self, name) for name in self.__class__.attributes}
        kws.update(kwargs)
        return self.__class__(**kws)

    def __repr__(self):
        return "{}: {}".format(
            self.__class__.__name__, {name: getattr(self, name) for name in self.__class__.attributes.keys()}
        )

    def __str__(self):
        return repr(self)

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            raise TypeError("Cannot compare different entities")
        for attribute in self.__class__.attributes.keys():
            if getattr(self, attribute) != getattr(other, attribute):
                return False
        return True


class Entity(AbstractEntity):
    id = IdAttribute()


# class DbStructure(object):    #Todo
# 	def __init__(self, **entities):
# 		self.entities=entities
#
# 	def addEntity(self, entity):
# 		self.entities[entity.__realName__]=entity


# Events


class AbstractEvent(object):
    def __init__(self):
        pass


# Events of database
class OpenDbEvent(AbstractEvent):
    pass


class CloseDbEvent(AbstractEvent):
    pass


class AddContainerEvent(AbstractEvent):
    def __init__(self, containerId):
        AbstractEvent.__init__(self)
        self.containerId = containerId


# Events of containers
class AbstractItemEvent(AbstractEvent):
    def __init__(self, itemId):
        AbstractEvent.__init__(self)
        self.itemId = itemId


class AddItemEvent(AbstractItemEvent):
    pass


class InsertItemEvent(AbstractItemEvent):
    pass


class SetItemEvent(AbstractItemEvent):
    pass


class GetItemEvent(AbstractItemEvent):
    pass


class RemoveItemEvent(AbstractItemEvent):
    pass


class AddItemsEvent(AbstractEvent):
    def __init__(self, itemIds):
        AbstractEvent.__init__(self)
        self.itemIds = itemIds


class GetItemsEvent(AbstractEvent):
    pass


class FilterItemsEvent(AbstractEvent):
    def __init__(self, func, itemIds):
        AbstractEvent.__init__(self)
        self.func = func
        self.itemIds = itemIds


class UpdateEvent(AbstractEvent):
    pass


class ClearEvent(AbstractEvent):
    pass


# Event Filters (e.g. for logging, or for Updating an UI)


class _AbstractEventFilter(object):
    def filterEvent(self, event):
        raise NotImplementedError()


class AbstractDatabaseEventFilter(_AbstractEventFilter):
    def __init__(self, database):
        _AbstractEventFilter.__init__(self)
        self.database = database

    def filterEvent(self, event):
        _AbstractEventFilter.filterEvent(self, event)


class AbstractContainerEventFilter(_AbstractEventFilter):
    def __init__(self, container):
        _AbstractEventFilter.__init__(self)
        self.container = container

    def filterEvent(self, event):
        _AbstractEventFilter.filterEvent(self, event)


# Engines


class AbstractDatabaseEngine(object, metaclass=ABCMeta):
    def __init__(self):
        self.database = None

    @abstractmethod
    def open(self, *args, **kwargs):
        pass

    @abstractmethod
    def close(self, *args, **kwargs):
        pass

    @abstractmethod
    def checkAccess(self):
        pass

    @abstractmethod
    def commit(self):
        pass

    def addContainer(self, container):
        pass

    @abstractmethod
    def createContainerEngine(self, container):
        return AbstractContainerEngine(container)


class AbstractContainerEngine(object, metaclass=ABCMeta):
    def __init__(self, container):
        self.container = container

    @abstractmethod
    def addItems(self, items):
        for item in items:
            yield item.id

    @abstractmethod
    def insertItems(self, items):
        pass

    @abstractmethod
    def getItem(self, itemId):
        return AbstractEntity(id=itemId)

    @abstractmethod
    def getItems(self, itemIds):
        for itemId in itemIds:
            return AbstractEntity(id=itemId)

    @abstractmethod
    def setItems(self, items):
        pass

    @abstractmethod
    def removeItems(self, itemIds):
        pass

    @abstractmethod
    def filterItems(self, check):
        return filter(None, [])

    @abstractmethod
    def itemIds(self):
        raise NotImplementedError()

    def addItem(self, item):
        return next(self.addItems([item]))

    def insertItem(self, item):
        self.insertItems(item)

    def setItem(self, item):
        self.setItems(item)

    def removeItem(self, itemId):
        self.removeItems(itemId)

    def allItems(self):
        return self.getItems(self.itemIds())

    def itemCount(self):
        return len(list(self.itemIds()))

    def checkItemExists(self, itemId):
        return itemId in self.itemIds()

    def clear(self):
        self.removeItems(self.itemIds())

    def update(self):
        pass

    @property
    def mainEngine(self):
        return self.container.database.engine


# Database object


class Database(object):
    """
    Abstraction of a Database
    """

    def __init__(self, engine=None):
        self.containers = {}
        self._engine = None
        self._eventFilters = []
        self._open = False
        if engine:
            self.setEngine(engine)

    def open(self, *args, **kwargs):
        """Opens the database, and returns if it was created newly"""
        new = self.engine.open(*args, **kwargs)
        self._open = True
        self.postEvent(OpenDbEvent())
        return new

    def close(self, *args, **kwargs):
        """Closes the database"""
        self.engine.close(*args, **kwargs)
        self._open = False
        self.postEvent(CloseDbEvent())

    @contextlib.contextmanager
    def do(self):
        """A context manager which updates all containers before,
        and commits everything afterwards"""

        # try: yield
        # except: self.rollback()
        # else: self.commit()

        # self.updateAll()
        yield
        self.commit()

    @property
    def isOpen(self):
        """Returns whether the db has been opened"""
        return self._open

    def updateAll(self):
        """Updates every container of the database"""
        for container in self.containers.values():
            container.update()

    def clearAll(self):
        """Clears every container in the database"""
        for container in self.containers.values():
            container.clear()

    def commit(self):
        """Makes sure, all changes are committed"""
        self.engine.commit()

    def checkAccess(self):
        """Checks, if the database is accessible (i.e. isOpen)"""
        if not self.isOpen:
            raise AccessError()
        self.engine.checkAccess()

    def engine(self):
        """The engine which does all the ItemManagement (storage, ids, etc.)"""
        return self._engine

    def setEngine(self, engine):
        if self.isOpen:
            raise RuntimeError(
                "Database already has an Engine;" "if you want to change it, close the db, set the engine and reopen it"
            )
        self._engine = engine
        self._engine.database = self

    engine = property(engine, setEngine)

    def registerEntity(self, entityCls):
        if self.isOpen:
            raise RuntimeError("Cannot register Entities when DB is already opened.")
        container = ItemContainer(self, entityCls)
        self.addContainer(container)
        return container

    def addContainer(self, container):
        containerId = self.containers[container.entityCls.__realName__] = container
        self.engine.addContainer(container)
        self.postEvent(AddContainerEvent(containerId))

    def currentDateTime(self):  # Reimplement (if u want)
        return datetime.datetime.now()

    def addEventFilter(self, eventFilter):
        self._eventFilters.append(eventFilter)

    def removeEventFilter(self, eventFilter):
        self._eventFilters.remove(eventFilter)

    def postEvent(self, event):
        for eventFilter in self._eventFilters:
            eventFilter.filterEvent(event)


def _requiresAccess(func):
    @functools.wraps(func)
    def wrapper(container, *args, **kwargs):
        container.database.checkAccess()
        return func(container, *args, **kwargs)

    return wrapper


class ItemContainer(object):
    """Represents a (SQL-) Table"""

    def __init__(self, database, entityCls):
        """Initializes a new ItemContainer object

        this should only be done by the corresponding database object
        (via db.registerEntity())
        :param database: a database object
        :param entityCls: an Entity class holding all the attributes
        """
        if "id" not in entityCls.attributes:
            raise RuntimeError("ItemContainer only accepts Entities WITH an id (i.e. primary key)")
        self.database = database
        self.entityCls = entityCls
        self._engine = self.database.engine.createContainerEngine(self)
        self._engine.container = self
        self._eventFilters = []
        self._refAttrs = {
            name: attr.entityCls.__realName__
            for name, attr in self.entityCls.attributes.items()
            if isinstance(attr, ReferenceAttribute)
        }

    def _getRefs(self, item):
        dic = {}
        for name, container in self._refAttrs.items():
            if getattr(item, name) is not None:
                dic[name] = self.database.containers[container].getItem(getattr(item, name))
        return item.copy(**dic)

    def _setRefs(self, item):
        dic = {}
        for name, container in self._refAttrs.items():
            val = getattr(item, name)
            if val is None:
                continue
            if val.id == Entity.id.default:  # The id was not specifically assigned
                dic[name] = self.database.containers[container].addItem(val)
            else:
                dic[name] = self.database.containers[container].setItem(val)
        return item.copy(**dic)

    @_requiresAccess
    def addItem(self, item):
        """Adds an item to this container

        the original id of the item object is discarded
        :param item: an instance of the EntityCls
        :return: the assigned id (integer)
        """
        item.id = self.engine.addItem(self._setRefs(item))
        self.postEvent(AddItemEvent(item.id))
        return item.id

    @_requiresAccess
    def addItems(self, *items):  # For fake data
        if hasattr(items[0], "__iter__") and len(items) == 1:
            items = items[0]
        itemIds = self.engine.addItems(map(self._setRefs, items))
        # self.postEvent(AddItemsEvent(itemIds))    #would empty itemIds generator  #Todo
        return itemIds

    @_requiresAccess
    def insertItem(self, item):
        """Inserts an Item at position item.id
        there should not be a previous item with this id

        :param item: an instance of the EntityCls
        """
        self.engine.insertItem(self._setRefs(item))
        self.postEvent(InsertItemEvent(item.id))
        return item.id

    @_requiresAccess
    def insertItems(self, *items):
        if hasattr(items[0], "__iter__") and len(items) == 1:
            items = items[0]
        self.engine.insertItems(map(self._setRefs, items))
        # self.postEvent(InsertItemEvent())

    @_requiresAccess
    def getItem(self, itemId):
        """Fetches an item from the database with the given id

        :param itemId: the id of the item
        :return: an instance of the EntityCls
        """
        item = self._getRefs(self.engine.getItem(itemId))
        self.postEvent(GetItemEvent(itemId))
        return item

    @_requiresAccess
    def getItems(self, *itemIds):
        if hasattr(itemIds[0], "__iter__") and len(itemIds) == 1:
            itemIds = itemIds[0]
        items = map(self._getRefs, self.engine.getItems(itemIds))
        self.postEvent(GetItemsEvent())
        return items

    @_requiresAccess
    def setItem(self, item):
        """Overwrites ('updates') an existing item at position item.id

        :param item: an instance of the EntityCls
        """
        self.engine.setItem(self._setRefs(item))
        self.postEvent(SetItemEvent(item.id))
        return item.id

    @_requiresAccess
    def removeItem(self, itemId):
        """Removes an item from the database

        :param itemId: the id of the item which should be removed
        """
        self.engine.removeItem(itemId)
        self.postEvent(RemoveItemEvent(itemId))

    @_requiresAccess
    def filterItems(self, check):
        """Filters items by condition

        :param check: a callable returning True or False; given an item
        :return: an iterable of all items where check returned True
        """
        items = map(self._getRefs, self.engine.filterItems(check))
        # self.postEvent(FilterItemsEvent(check, [item.id for item in items]))    #Todo: Here's the problem
        return items

    @_requiresAccess
    def clear(self):
        """Clears this container, i.e empties it"""
        self.engine.clear()
        self.postEvent(ClearEvent())

    def update(self):
        """Makes sure all items are up-to-date

        Calling this is useless for some engines, but though recommended
        """
        self.engine.update()
        self.postEvent(UpdateEvent())

    def itemIds(self):
        """Returns all ids of all items

        :return: an iterable of ints
        """
        return self.engine.itemIds()

    @_requiresAccess
    def allItems(self):
        """Returns an iterator of all items

        :return: iterable
        """
        items = map(self._getRefs, self.engine.allItems())
        self.postEvent(GetItemsEvent())
        return items

    @property
    def engine(self):
        """Returns the underlying subengine object

        :return: AbstractContainerEngine
        """
        return self._engine

    def addEventFilter(self, eventFilter):
        """Adds an event filter

        :param eventFilter: an object with a 'filterEvent' method
        """
        self._eventFilters.append(eventFilter)

    def removeEventFilter(self, eventFilter):
        """Removes an event filter

        :param eventFilter: an object with a 'filterEvent' method
        """
        self._eventFilters.remove(eventFilter)

    def postEvent(self, event):
        """Posts an event

        All EventFilter.filterEvent methods are called
        :param event: an AbstractEvent
        """
        for eventFilter in self._eventFilters:
            eventFilter.filterEvent(event)

    # @requiresAccess
    def __len__(self):
        return self.engine.itemCount()

    def __iter__(self):
        return iter(self.allItems())

    def __getitem__(self, key):
        return self.getItem(key)

    def __setitem__(self, key, value):
        self.setItem(key, value)

    def __delitem__(self, itemId):
        self.removeItem(itemId)

    # @requiresAccess
    def __contains__(self, itemOrId):
        if isinstance(itemOrId, Entity):
            return self.engine.checkItemExists(itemOrId.id)
        return self.engine.checkItemExists(itemOrId)

    def __repr__(self):
        return "{name} [{rName}]: {c}".format(
            name=self.entityCls.__containerName__, rName=self.entityCls.__realName__, c=len(self)
        )

    def __str__(self):
        return self.entityCls.__containerName__
