from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import relationship

from . import db_access

#########################################################
# Access

GROUP_TYPE_LEADERBOARD = 0


class GroupAccess(db_access.Base):
    __tablename__ = "group_access"

    id = Column(Integer, primary_key=True, index=True)
    slug = Column(String, unique=True, index=True)
    name = Column(String)
    description = Column(String)
    icon = Column(String)
    type = Column(Integer)


class UserAccess(db_access.Base):
    __tablename__ = "user_access"

    id = Column(Integer, primary_key=True, index=True)
    login_identifier = Column(String)
    login_type = Column(String)
    login_status = Column(Integer)
    password_hashed = Column(String)


class UserDetail(db_access.Base):
    __tablename__ = "user_detail"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_access.id", ondelete="CASCADE"))
    name = Column(String)
    sex = Column(String)
    meta = Column(String)

    user = relationship(UserAccess, foreign_keys=[user_id])


class UserSession(db_access.Base):
    __tablename__ = "user_session"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("user_access.id", ondelete="CASCADE"))
    token = Column(String, unique=True, index=True)
    create_time = Column(DateTime)
    expiry_time = Column(DateTime)
    last_active_time = Column(DateTime)
    platform = Column(String)
    version = Column(String)
    build_version = Column(String)
    source_ip = Column(String)
    meta = Column(String)

    user = relationship(UserAccess, foreign_keys=[user_id])


ACCESS_TYPE_READ = 0
ACCESS_TYPE_WRITE = 1
ACCESS_TYPE_ADMIN = 2


class GroupUserAccess(db_access.Base):
    __tablename__ = "group_user_access"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_access.id", ondelete="CASCADE"))
    group_id = Column(Integer, ForeignKey("group_access.id", ondelete="CASCADE"))
    type = Column(Integer)

    user = relationship(UserAccess, foreign_keys=[user_id])
    group = relationship(GroupAccess, foreign_keys=[group_id])


###################################
# Audit

# JH_EVENT_LOGIN = 0
# JH_EVENT_LOGOFF = 1
# JH_EVENT_LOGIN_IMPERSONATE = 2

# class LoginHistory(db_coach.Base):
#     __tablename__ = "login_history"

#     id = Column(Integer, primary_key=True)
#     time_created = Column(DateTime(timezone=True), server_default=func.now())
#     event_type = Column(Integer)
#     username = Column(String)
#     message = Column(String)
#     meta = Column(String)

######################################
# Data

GROUP_TYPE_LEADERBOARD = 0


class RankResults(db_access.Base):
    __tablename__ = "rank_results"

    id = Column(Integer, primary_key=True, index=True)
    time = Column(DateTime)
    win_user_id = Column(Integer)
    loss_user_id = Column(Integer)
    owner_id = Column(Integer, ForeignKey("user_access.id", ondelete="CASCADE"))
    group_id = Column(Integer, ForeignKey("group_access.id", ondelete="CASCADE"))
    comments = Column(String)
    meta = Column(String)

    owner = relationship(UserAccess, foreign_keys=[owner_id])
    group = relationship(GroupAccess, foreign_keys=[group_id])


# Store the baselines here


class RankSnapshot(db_access.Base):
    __tablename__ = "rank_snapshot"

    id = Column(Integer, primary_key=True, index=True)
    group_id = Column(Integer, ForeignKey("group_access.id", ondelete="CASCADE"))
    time = Column(DateTime)

    group = relationship(GroupAccess, foreign_keys=[group_id])


class RankSnapshotDetail(db_access.Base):
    __tablename__ = "rank_snapshot_detail"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("user_access.id", ondelete="CASCADE"))
    rank_snapshot_id = Column(
        Integer, ForeignKey("rank_snapshot.id", ondelete="CASCADE")
    )
    rank = Column(Integer)

    user = relationship(UserAccess, foreign_keys=[user_id])
    rank_snapshot = relationship(RankSnapshot, foreign_keys=[rank_snapshot_id])
