from datetime import datetime


from . import db
from .util import (
    custom_logging,
)

LOGGING_ID = "CacheUser"
LOGGER = custom_logging.getLogger(LOGGING_ID)

###################################################
# Basic Cache with expiry

# Object will be re-loaded afer this
TTL_TIMEOUT = 60  # Seconds

FEATURE_PREFIX = "f_"


class UserCacheOb(object):
    def __init__(self, username, user_id=None):
        self.username = username
        self.user_id = user_id
        self.ttl_time = None
        self.user = None
        self.detail = None
        self.checkTTL()

    def checkTTL(self):
        if (
            self.ttl_time is None
            or (datetime.now() - self.ttl_time).total_seconds() > TTL_TIMEOUT
        ):
            try:
                self.user, self.detail = self.init_data(self.username, self.user_id)
                if self.user:
                    self.username = self.user.login_identifier
                self.ttl_time = datetime.now()
                LOGGER.debug("UserCache Load: " + self.username)
            except Exception as ex:
                LOGGER.exception("UserCache Load Failed", exc_info=ex)

    def is_valid(self) -> bool:
        return self.user is not None

    def get_user(self):
        self.checkTTL()
        return self.user

    def get_user_detail(self):
        self.checkTTL()
        return self.detail

    def get_login_name(self):
        self.checkTTL()
        if self.user:
            return self.user.login_identifier
        return None

    def get_user_id(self):
        self.checkTTL()
        if self.user:
            return self.user.id
        return None

    def get_user_name(self):
        self.checkTTL()
        if self.detail:
            return self.detail.name
        if self.user:
            return UserCacheOb.format_user(self.user.login_identifier)
        return None

    def get_user_name_full(self):
        self.checkTTL()
        if self.detail:
            return self.detail.name
        if self.user:
            return self.user.login_identifier
        return None

    @staticmethod
    def format_user(user: str):
        if user.find("@") == -1:
            return user
        # Attempt a username
        user = user.split("@")[0]
        return UserCacheOb.capitalize_words(user.replace(".", " "))

    @staticmethod
    def capitalize_words(sentence: str):
        return " ".join(word.capitalize() for word in sentence.split())

    @staticmethod
    def init_data(username, user_id):
        if user_id is not None:
            user = db.get_access().get_user_access_by_id(user_id)
        else:
            if username is None:
                return None, {}
            user = db.get_access().get_user_access(username)

        if user is None:
            return None, {}

        detail = db.get_access().get_user_detail(user.id)

        return user, detail


# Index both ways
g_user = {}
g_user_id = {}


def get_user_by_id(id: int) -> UserCacheOb:
    global g_user_id
    global g_user

    ob = None
    if id is not None:
        if id not in g_user_id.keys():
            ob = UserCacheOb(None, id)
            if ob.is_valid():
                g_user_id[id] = ob
                g_user[ob.get_login_name()] = ob
            else:
                ob = None
        else:
            ob = g_user_id[id]

    return ob


def get_user(username: str) -> UserCacheOb:
    global g_user_id
    global g_user

    ob = None
    if username is not None:
        if username not in g_user.keys():
            ob = UserCacheOb(username)
            if ob.is_valid():
                g_user[username] = ob
                g_user_id[ob.get_user().id] = ob
            else:
                ob = None
        else:
            ob = g_user[username]

    return ob


def invalidate_user(username) -> bool:
    global g_user_id
    global g_user

    if username is not None:
        if username in g_user.keys():
            if g_user[username].user_id in g_user_id.keys():
                del g_user_id[g_user[username].user_id]
            del g_user[username]
            return True

    return False
