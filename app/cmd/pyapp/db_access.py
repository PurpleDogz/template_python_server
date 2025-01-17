from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

from .util import config, db_util

engine = db_util.init_engine(
    config.get().DB_MODE,
    config.get().get_file_cache_folder(),
    config.get().DB_HOST,
    config.get().DB_NAME,
    config.get().DB_USERNAME,
    config.get().DB_PASSWORD,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

###################################################
# Database Interface


class Database(object):
    def __init__(self) -> None:
        pass
