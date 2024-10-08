class User(Entity):
    name = StringAttribute("")
    password = StringAttribute("")


class Group(Entity):
    name = StringAttribute("")


class Permission(Entity):
    Add, Get, Set, Remove = range(4)
    containerId = IntAttribute(-1)
    type = IntAttribute(-1, IntAttribute.Int8)


class Membership(Entity):
    userId = IntAttribute(-1)
    groupId = IntAttribute(-1)


class PermissionAssignment(Entity):
    groupId = IntAttribute(-1)
    permissionId = IntAttribute(-1)


class AuthenticationError(DatabaseError):
    pass


class PermissionError(DatabaseError):
    pass


class requiresPermission(object):
    def __init__(self, *permissionTypes):
        self.permissionTypes = permissionTypes

    def __call__(self, func):
        def wrapper(container, *args, **kwargs):
            container.database.checkUserPermissions(
                container.database.currentUser().id, container.id, *self.permissionTypes
            )
            return func(container, *args, **kwargs)

        return wrapper


class UAItemContainer(ItemContainer):
    def __init__(self, database, entityCls, name, realName=None):
        ItemContainer.__init__(self, database, entityCls, name, realName)

    def currentUser(self):
        return self.database.currentUser()

    addItem = requiresPermission(Permission.Add)(ItemContainer.addItem)
    getItem = requiresPermission(Permission.Add)(ItemContainer.getItem)
    setItem = requiresPermission(Permission.Add)(ItemContainer.setItem)

    @requiresPermission(Permission.Add)
    def addItem(self, item):
        return ItemContainer.addItem(self, item)

    @requiresPermission(Permission.Get)
    def getItem(self, itemId):
        return ItemContainer.getItem(self, itemId)

    @requiresPermission(Permission.Set)
    def setItem(self, item):
        ItemContainer.setItem(self, item)

    @requiresPermission(Permission.Remove)
    def removeItem(self, itemId):
        ItemContainer.removeItem(self, itemId)

    @requiresPermission(Permission.Get)
    def allItems(self):
        return ItemContainer.allItems(self)


class _UAContainer(UAItemContainer):  # Adds possibilities to do stuff secretly
    def addItemSecretly(self, item):
        return self.engine.addItem(item)

    def getItemSecretly(self, itemId):
        return self.engine.getItem(itemId)

    def allItemsSecretly(self):
        return self.engine.allItems()

    def filterItemsSecretly(self, check):
        return self.engine.filterItems(check)


class UADbClient(DbClient):
    def __init__(self, database, user):
        DbClient.__init__(self, database)
        self.user = user


class UADatabase(Database):
    def __init__(self, engine=None):
        Database.__init__(self, engine)
        self.users = _UAContainer(self, User, "Users")
        self.addContainer(self.users)
        self.groups = _UAContainer(self, Group, "Groups")
        self.addContainer(self.groups)
        self.permissions = _UAContainer(self, Permission, "Permissions")
        self.addContainer(self.permissions)
        self.memberships = _UAContainer(self, Membership, "Memberships")
        self.addContainer(self.memberships)
        self.permissionAssignments = _UAContainer(self, PermissionAssignment, "Permission Assignments")
        self.addContainer(self.permissionAssignments)

    def registerEntity(self, entityCls, name, realName=None):
        if self.isOpen:
            raise RuntimeError("Cannot register Entities when DB is already opened.")
        container = UAItemContainer(self, entityCls, name, realName)
        self.addContainer(container)
        return container

    def login(self, userName, password):
        user = self.checkUser(userName, password)
        client = UADbClient(self, user)
        self.addClient(client)
        return client

    def currentUser(self):
        return self.currentClient.user

    # def log(self, type):
    # 	self.logBook.addItem(UALogEntry(type, self.currentUser().id, self.currentDateTime()))
    #
    # def itemLog(self, type, itemId):
    # 	self.logBook.addItem(UAItemLogEntry(type, itemId, self.currentUser().id, self.currentDateTime()))

    def initAdminGroup(self, userName, password, groupName):
        userId = self.users.addItemSecretly(User(name=userName, password=password))
        groupId = self.groups.addItemSecretly(Group(name=groupName))
        self.memberships.addItemSecretly(Membership(userId=userId, groupId=groupId))
        for container in self.containers:
            for permissionType in (Permission.Add, Permission.Get, Permission.Set, Permission.Remove):
                permissionId = self.permissions.addItemSecretly(
                    Permission(containerId=container.id, type=permissionType)
                )
                self.permissionAssignments.addItemSecretly(
                    PermissionAssignment(groupId=groupId, permissionId=permissionId)
                )
        return userId, groupId

    def getUserByName(self, userName):
        for user in self.users.filterItemsSecretly(lambda usr: usr.name == userName):
            return user
        raise ItemError(-2)

    def getUserGroupsIds(self, userId):
        return [
            membership.groupId
            for membership in self.memberships.filterItemsSecretly(lambda membership: membership.userId == userId)
        ]

    def getGroupPermissionsIds(self, groupId):
        return [
            assignment.permissionId
            for assignment in self.permissionAssignments.filterItemsSecretly(
                lambda assignment: assignment.groupId == groupId
            )
        ]

    def checkUser(self, userName, password):
        try:
            user = self.getUserByName(userName)
        except ItemError:
            raise AuthenticationError() from None
        if not user.password == password:
            raise AuthenticationError()
        return user

    def checkUserPermissions(self, userId, containerId, *permissionTypes):
        users = self.users.allItemsSecretly()
        groups = self.groups.allItemsSecretly()
        permissions = self.permissions.allItemsSecretly()
        permAss = self.permissionAssignments.allItemsSecretly()
        membs = self.memberships.allItemsSecretly()
        perms = 0
        for groupId in self.getUserGroupsIds(userId):
            for permissionId in self.getGroupPermissionsIds(groupId):
                permission = self.permissions.getItemSecretly(permissionId)
                if (permission.type in permissionTypes) and (permission.containerId == containerId):
                    perms += 1
        if perms < len(permissionTypes):
            raise PermissionError()
        return userId
