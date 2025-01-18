from datetime import datetime, timedelta, timezone
from . import db, models_access
from .util import custom_logging, config

LOGGING_ID = "CacheSession"
LOGGER = custom_logging.getLogger(LOGGING_ID)

###################################################
# Basic Cache for now, eventually will be Redis, etc


class CacheSession(object):
    def __init__(self):
        pass

    def allocate_session_id(self, username) -> int:
        user = db.get_access().get_user_access(username)

        if not user:
            LOGGER.error("Allocate Session Fail: User not found: {}".format(username))
            return None

        try:
            for c in db.get_access_db():
                create_time = datetime.now(timezone.utc)
                expiry_time = datetime.now(timezone.utc) + timedelta(
                    seconds=config.get().ACCESS_TOKEN_EXPIRY_SECONDS
                )
                session = models_access.UserSession(
                    user_id=user.id,
                    create_time=create_time,
                    expiry_time=expiry_time,
                    last_active_time=create_time,
                )
                c.add(session)
                c.flush()
                c.commit()
                return session.id
        except Exception as ex:
            LOGGER.exception("Allocate Session Fail: ", exc_info=ex)

        return None

    def get_session_by_id(self, session_id):
        for c in db.get_access_db():
            return (
                c.query(models_access.UserSession)
                .filter(models_access.UserSession.id == session_id)
                .first()
            )
        return None

    def get_session_by_token(self, token):
        for c in db.get_access_db():
            return (
                c.query(models_access.UserSession)
                .filter(models_access.UserSession.token == token)
                .first()
            )
        return None

    def remove_session_by_id(self, session_id):
        for c in db.get_access_db():
            c.query(models_access.UserSession).filter(
                models_access.UserSession.id == session_id
            ).delete()
            c.commit()

    def remove_session_by_token(self, token):
        for c in db.get_access_db():
            c.query(models_access.UserSession).filter(
                models_access.UserSession.token == token
            ).delete()
            c.commit()

    def set_session(
        self,
        session_id,
        token,
        username,
        platform=None,
        version=None,
        build_version=None,
        source_ip=None,
        meta=None,
    ) -> bool:
        try:
            user = db.get_access().get_user_access(username)

            if not user:
                LOGGER.error("Set Session Fail: User not found: {}".format(username))
                return False

            session = self.get_session_by_id(session_id)

            if not session:
                LOGGER.warning(
                    "Set Session Fail: Session not found: {} ({})".format(
                        session_id, username
                    )
                )
                return False

            for c in db.get_access_db():
                s_lookup = (
                    c.query(models_access.UserSession)
                    .filter(models_access.UserSession.id == session.id)
                    .first()
                )
                if token:
                    s_lookup.token = token
                if platform:
                    s_lookup.platform = platform
                if version:
                    s_lookup.version = version
                if build_version:
                    s_lookup.build_version = build_version
                if source_ip:
                    s_lookup.source_ip = source_ip
                if meta:
                    s_lookup.meta = meta
                LOGGER.debug("Set Session: Update session: {}".format(username))
                c.flush()
                c.commit()
                return True
        except Exception as ex:
            LOGGER.exception("Set Session Fail: ", exc_info=ex)
        return False


g_sc = None

def get() -> CacheSession:
    global g_sc
    if g_sc is None:
        g_sc = CacheSession()
    return g_sc
