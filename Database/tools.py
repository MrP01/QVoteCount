import time


def measure(repeat, func, *args, **kwargs):
    startTime = time.time()
    for i in range(repeat):
        func(*args, **kwargs)
    return time.time() - startTime


class convertTo(object):
    def __init__(self, type):
        self.type = type

    def __call__(self, fun):
        def wrapper(*args, **kwargs):
            ret = fun(*args, **kwargs)
            return self.type(ret)

        return wrapper


def countGen(iterator, l):
    for item in iterator:
        yield item
        l[0] += 1


def createEmptyFile(path):
    open(path, "w").close()


def isinstancePool(obj, types):
    for type_ in types.keys():
        if isinstance(obj, type_):
            return types[type_]


def codeInjectionGen(iterable, before=lambda x: x, after=lambda x: x):
    for item in iterable:
        before(item)
        yield item
        after(item)


class Item(object):
    pass


class ItemStorage(object):
    def __init__(self):
        self._data = dict()

    def addItem(self, item):
        item.id = self.nextItemId()
        self._data[item.id] = item
        return item.id

    def insertItem(self, item):
        self._data[item.id] = item

    def setItem(self, item):
        self._data[item.id] = item

    def getItem(self, itemId):
        return self._data[itemId]

    def removeItem(self, itemId):
        del self._data[itemId]

    def ids(self):
        return self._data.keys()

    def items(self):
        return self._data.values()

    def filter(self, check):
        return filter(check, self.items())

    def clear(self):
        self._data.clear()

    def nextItemId(self):
        try:
            return max(self.ids()) + 1
        except ValueError:
            return 0

    def __len__(self):
        return len(self._data)

    def __iter__(self):
        return iter(self.items())

    def __getitem__(self, key):
        return self.getItem(key)

    def __setitem__(self, key, value):
        self.setItem(value)

    def __delitem__(self, itemId):
        self.removeItem(itemId)

    def __contains__(self, item):
        return item.id in self.ids()

    def __str__(self):
        return "ItemStorage: %s" % str(self._data)
