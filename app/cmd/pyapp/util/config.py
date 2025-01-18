"""Central place to setup needed config

All config via environment variables for now
"""

import os
import uuid
from datetime import datetime, timezone

from pydantic import BaseSettings

_config_cache = None

TRUE = "TRUE"
FALSE = "FALSE"

DB_MODE_SQLITE = "sqlite"
DB_MODE_POSTGRESQL = "postgresql"

COOKIE_IMPERSONATE = "impersonate"
COOKIE_GROUP = "group"

DEPLOYMENT_MODE_PRODUCTION = "production"
DEPLOYMENT_MODE_STAGING = "staging"
DEPLOYMENT_MODE_DEVELOPMENT = "development"

DEPLOYMENT_ACCESS_MODE_CLOSED = "closed"
DEPLOYMENT_ACCESS_MODE_FREEMIUM = "freemium"
DEPLOYMENT_ACCESS_MODE_OPEN = "open"

DEPLOYMENT_LOGIN_MODE_ANY = "any"
DEPLOYMENT_LOGIN_MODE_BASIC_AUTH = "basic_auth"
DEPLOYMENT_LOGIN_MODE_OAUTH = "oauth"


class ServiceConfig(BaseSettings):
    STARTUP_TS: datetime = datetime.now(timezone.utc)
    SERVICE_HOST: str = "DEFAULT"
    SERVICE_BASE_NAME: str = "PYTHON_SERVER"
    SERVICE_NAME: str = "olympia"
    DB_NAME: str = "python_server"
    SERVICE_MODE: str = "ADMIN"
    SERVICE_NODE_ID: str = str(uuid.uuid4())
    DEFAULT_TIMEZONE: str = "Australia/Melbourne"
    DATA_FOLDER: str = ""

    ACCESS_EMAIL_DOMAINS: str = ""

    DEPLOYMENT_ACCESS_MODE: str = DEPLOYMENT_ACCESS_MODE_OPEN
    DEPLOYMENT_MODE: str = DEPLOYMENT_MODE_PRODUCTION
    LOGIN_MODE: str = DEPLOYMENT_LOGIN_MODE_OAUTH

    ICON_NAME: str = "default.png"
    MSG_LIMITED_ACCESS_ERROR: str = "Invalid Access"

    APP_HOST_URL: str = ""

    HOST_ADDRESS: str = "0.0.0.0"
    PORT: str = "9193"
    PORT_INTERNAL_API: str = "8051"

    USER_URLS: list = [""]

    ACCESS_TOKEN_EXPIRY_SECONDS: int = 24 * 60 * 60 * 14  # 14 Days
    ACCESS_SECRET: str = ""

    DB_MODE: str = DB_MODE_POSTGRESQL
    DB_HOST: str = "localhost:5432"
    DB_USERNAME: str = "postgres"
    DB_PASSWORD: str = "postgres"

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_FORCE_HTTPS_REDIRECT: str = TRUE

    MESSAGE_SERVICE_HOST: str = "localhost:4150"

    ENABLE_PERF_LOGGING_UX: str = TRUE

    ENABLE_OB_LOGGING: str = FALSE

    class Config:
        extra = "allow"

    def get_startup_ts(self) -> datetime:
        return self.STARTUP_TS

    def get_file_cache_folder(self) -> str:
        return self.DATA_FOLDER + "/cache"

    def get_logs_folder(self) -> str:
        return self.DATA_FOLDER + "/logs/"

    def get_log_file_name(self) -> str:
        return self.SERVICE_NAME

    def get_app_url(self) -> str:
        if len(self.APP_HOST_URL) == 0:
            return "/"
        return self.APP_HOST_URL + "/"

    def get_cookie_name(self) -> str:
        return "access_" + self.SERVICE_BASE_NAME

    def check_deployment_access_mode(self, mode: str) -> bool:
        return self.DEPLOYMENT_ACCESS_MODE == mode


def get(cfg=None) -> ServiceConfig:
    global _config_cache
    if not _config_cache:
        _config_cache = ServiceConfig.parse_obj(dict(os.environ))
        if cfg:
            _config_cache.parse_obj(cfg)
    return _config_cache
