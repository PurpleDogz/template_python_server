from . import db_access, db_access_imp

###################################################
# coach Database Instance

db_access.Base.metadata.create_all(bind=db_access.engine)

_database_coach = None


def get_access() -> db_access_imp.Database:
    global _database_coach
    if not _database_coach:
        _database_coach = db_access_imp.Database()
    return _database_coach


def get_access_db():
    try:
        db = db_access.SessionLocal()
        yield db
    finally:
        db.close()
