import json
from datetime import datetime
from . import db, db_access, models_access, constants, cache_user
from .util import custom_logging, config
from .model import rank
from dataclasses import dataclass
from dataclasses_json import dataclass_json
from sqlalchemy import desc, func, or_
import os


LOGGING_ID = "AccessDB"
LOGGER = custom_logging.getLogger(LOGGING_ID)

###################################################
# Database


def parseInt(v):
    if v and str(v).isnumeric():
        return int(v)
    return None


def get_meta(msg, field="meta"):
    if field in msg.keys():
        return json.dumps(msg[field]) if isinstance(msg[field], dict) else msg[field]
    return ""


# Helper Class
@dataclass_json
@dataclass
class ServerMetrics:
    source: str = None
    source_type: int = 0
    uptime: int = 0
    cpu_pct: int = 0
    memory_usage: int = 0
    memory_total: int = 0
    memory_pct: int = 0
    disk_usage: int = 0
    disk_total: int = 0
    disk_pct: int = 0
    network_in: int = 0
    network_out: int = 0


def get_value(r, key, default=""):
    return r[key] if key in r.keys() else default


class Database(db_access.Database):
    def __init__(self) -> None:
        pass

    def init_db_defaults(self):
        LOGGER.info("DB: Check Defaults")

        # default_json = "{}/general/{}".format(config.get().DATA_FOLDER, "ranking.json")

        # if os.path.exists(default_json):
        #     try:
        #         with open(default_json, "r") as f:
        #             j = json.load(f)
        #             for k in j.keys():
        #                 LOGGER.info("DB: Loading Ranking for " + k)
        #                 group_access = self.get_group_access(k)
        #                 if group_access:
        #                     for c in db.get_access_db():
        #                         c.query(models_access.RankSnapshot).filter(
        #                             models_access.RankSnapshot.group_id
        #                             == group_access.id
        #                         ).delete()
        #                         c.commit()

        #                     user_rankings = []

        #                     for u in j[k]:
        #                         user = cache_user.get_user(u["username"])
        #                         if user:
        #                             user_rankings.append(user.get_user_id())
        #                         else:
        #                             LOGGER.error(
        #                                 "Ranking Error: User '{}' not found in group '{}'".format(
        #                                     u["username"], k
        #                                 )
        #                             )

        #                     self.add_rank_snapshot(datetime.now(), k, user_rankings)

        #     except Exception as ex:
        #         LOGGER.error("Error in ranking.json -> {}".format(str(ex)))
        #         pass
        # else:
        #     LOGGER.info("No ranking.json file found")

    # Check with the login auth type also
    def check_user_login_access(self, username, login_type=None) -> bool:
        for c in db.get_access_db():
            q = c.query(models_access.UserAccess)
            q = q.filter(
                func.lower(models_access.UserAccess.login_identifier)
                == func.lower(username)
            )
            if login_type:
                q = q.filter(
                    or_(
                        models_access.UserAccess.login_type == login_type,
                        models_access.UserAccess.login_type == constants.LOGIN_MODE_ANY,
                    )
                )
            q = q.filter(
                models_access.UserAccess.login_status.in_(
                    constants.LOGIN_ACCESS_ENABLED
                )
            )
            if q.first() is not None:
                return True

        return False

    def get_user_access(self, username: str, group: str = None):
        for c in db.get_access_db():
            q = c.query(models_access.UserAccess)
            if group:
                q = q.join(
                    models_access.GroupUserAccess,
                    models_access.GroupUserAccess.user_id
                    == models_access.UserAccess.id,
                )
                q = q.filter(
                    func.lower(models_access.GroupAccess.slug) == func.lower(group)
                )
            q = q.filter(
                func.lower(models_access.UserAccess.login_identifier)
                == func.lower(username)
            )
            return q.first()
        return None

    def get_user_access_groups(self, username: str):
        for c in db.get_access_db():
            q = c.query(models_access.GroupAccess)
            q = q.join(
                models_access.GroupUserAccess,
                models_access.GroupAccess.id == models_access.GroupUserAccess.group_id,
            )
            q = q.join(
                models_access.UserAccess,
                models_access.GroupUserAccess.user_id == models_access.UserAccess.id,
            )
            q = q.filter(
                func.lower(models_access.UserAccess.login_identifier)
                == func.lower(username)
            )
            return q.all()
        return None

    def get_user_access_by_id(self, id: int, group: str = None):
        for c in db.get_access_db():
            q = c.query(models_access.UserAccess)
            if group:
                q = q.join(
                    models_access.GroupUserAccess,
                    models_access.GroupUserAccess.user_id
                    == models_access.UserAccess.id,
                )
                q = q.filter(
                    func.lower(models_access.GroupAccess.slug) == func.lower(group)
                )
            q = q.filter(models_access.UserAccess.id == id)
            return q.first()
        return None

    def get_group_access(self, slug) -> models_access.GroupAccess:
        for c in db.get_access_db():
            q = c.query(models_access.GroupAccess)
            q = q.filter(func.lower(models_access.GroupAccess.slug) == func.lower(slug))
            return q.first()
        return None

    def get_group_user_count(self, group: str):
        for c in db.get_access_db():
            q = c.query(models_access.UserAccess)
            q = q.join(
                models_access.GroupUserAccess,
                models_access.GroupUserAccess.user_id == models_access.UserAccess.id,
            )
            q = q.filter(
                func.lower(models_access.GroupAccess.slug) == func.lower(group)
            )
            return q.count()
        return 0

    def get_group_users(self, slug):
        for c in db.get_access_db():
            q = c.query(models_access.UserAccess)
            q = q.join(
                models_access.GroupUserAccess,
                models_access.GroupUserAccess.user_id == models_access.UserAccess.id,
            )
            q = q.filter(func.lower(models_access.GroupAccess.slug) == func.lower(slug))
            q = q.order_by(models_access.UserAccess.login_identifier)
            ret = []
            for e in q.all():
                u = cache_user.get_user_by_id(e.id)
                if u:
                    ret.append(
                        {
                            "username": u.get_user_name(),
                            "user_name_full": u.get_user_name_full(),
                            "id": e.id,
                        }
                    )
            return ret
        return []

    def set_user_group(self, username, group):
        if self.get_user_access(username, group):
            # Already in group
            return True

        user = self.get_user_access(username)
        group_access = self.get_group_access(group)

        if user and group_access:
            for c in db.get_access_db():
                c.add(
                    models_access.GroupUserAccess(
                        user_id=user.id, group_id=group_access.id
                    )
                )
                c.commit()
            return True
        return False

    def get_user_detail(self, user_id: int):
        for c in db.get_access_db():
            q = c.query(models_access.UserDetail)
            q = q.filter(models_access.UserDetail.user_id == user_id)
            return q.first()
        return None

    def get_all_groups(self):
        for c in db.get_access_db():
            q = c.query(models_access.GroupAccess)
            q = q.order_by(models_access.GroupAccess.name)
            return q.all()
        return []

    def get_rank_results(
        self,
        slug,
        start_date=None,
        end_date=None,
        name_owner=None,
        participant_only=None,
        search_comment=None,
        resolve_names=True,
        limit=1000,
    ):
        filter_owner_id = None
        if name_owner:
            user = self.get_user_access(name_owner)
            if user:
                filter_owner_id = user.id

        filter_participant_id = None
        if participant_only:
            user = self.get_user_access(participant_only)
            if user:
                filter_participant_id = user.id

        for c in db.get_access_db():
            q = c.query(models_access.RankResults)
            q = q.join(
                models_access.GroupAccess,
                models_access.RankResults.group_id == models_access.GroupAccess.id,
            )
            q = q.filter(func.lower(models_access.GroupAccess.slug) == func.lower(slug))
            if start_date:
                q = q.filter(models_access.RankResults.time >= start_date)
            if end_date:
                q = q.filter(models_access.RankResults.time <= end_date)
            if filter_owner_id:
                q = q.filter(models_access.RankResults.owner_id == filter_owner_id)
            if search_comment:
                q = q.filter(
                    func.lower(models_access.RankResults.comments).like(
                        "%{}%".format(search_comment.lower())
                    )
                )
            if filter_participant_id:
                q = q.filter(
                    or_(
                        models_access.RankResults.win_user_id == filter_participant_id,
                        models_access.RankResults.loss_user_id == filter_participant_id,
                    )
                )
            q = q.order_by(desc(models_access.RankResults.time))
            q = q.limit(limit)

            ret = []
            for e in q.all():
                add = {
                    "id": e.id,
                    "time": e.time,
                    "win_user_id": e.win_user_id,
                    "loss_user_id": e.loss_user_id,
                    "owner_id": e.owner_id,
                    "comments": e.comments,
                    "meta": e.meta,
                }

                if resolve_names:
                    u = cache_user.get_user_by_id(e.win_user_id)
                    if u:
                        add["win_user"] = u.get_user_name()
                    u = cache_user.get_user_by_id(e.loss_user_id)
                    if u:
                        add["loss_user"] = u.get_user_name()
                    u = cache_user.get_user_by_id(e.owner_id)
                    if u:
                        add["owner"] = u.get_user_name()
                ret.append(add)
            return ret

        return None

    def add_result(self, username, slug, date, winner_id, loser_id, comment):
        user = self.get_user_access(username)

        if user:
            for c in db.get_access_db():
                c.add(
                    models_access.RankResults(
                        time=date,
                        win_user_id=winner_id,
                        loss_user_id=loser_id,
                        owner_id=user.id,
                        group_id=self.get_group_access(slug).id,
                        comments=comment,
                    )
                )
                c.commit()
            return True
        return False

    def delete_result(self, username, slug, id):
        user = self.get_user_access(username)

        delete_id = None

        for c in db.get_access_db():
            q = c.query(models_access.RankResults)
            q = q.join(
                models_access.GroupAccess,
                models_access.RankResults.group_id == models_access.GroupAccess.id,
            )
            q = q.filter(func.lower(models_access.GroupAccess.slug) == func.lower(slug))
            q = q.filter(models_access.RankResults.id == id)
            q = q.filter(models_access.RankResults.owner_id == user.id)
            if q.first():
                delete_id = q.first().id

        if delete_id:
            for c in db.get_access_db():
                q = c.query(models_access.RankResults)
                q = q.filter(models_access.RankResults.id == delete_id)
                q.delete()
                c.commit()
            return True

        return False

    def get_head_to_head(self, slug, username, start_date=None, end_date=None):
        results = self.get_rank_results(
            slug, start_date, end_date, None, username, None, True, None
        )

        user = self.get_user_access(username)

        if not user:
            return []

        map_opponents = {}

        for r in results:
            if r["win_user_id"] == user.id:
                entry = map_opponents.get(r["loss_user"], {"wins": 0, "losses": 0})
                entry["wins"] += 1
                map_opponents[r["loss_user"]] = entry
            else:
                entry = map_opponents.get(r["win_user"], {"wins": 0, "losses": 0})
                entry["losses"] += 1
                map_opponents[r["win_user"]] = entry

        for k in map_opponents.keys():
            entry = map_opponents[k]
            total = entry["wins"] - entry["losses"]
            if total == 0:
                entry["result"] = "Drawn"
            elif total > 0:
                entry["result"] = "Win"
            else:
                entry["result"] = "Loss"

        ret = []
        for k in map_opponents.keys():
            entry = map_opponents[k]
            entry["opponent"] = k
            ret.append(entry)

        ret = sorted(ret, key=lambda x: x["opponent"])

        return ret

    def get_leaderboard(self, slug, method, start_date=None, end_date=None):
        results = self.get_rank_results(slug, start_date, end_date)

        results_simple = []
        # print(results)
        for r in results:
            results_simple.append((r["win_user_id"], r["loss_user_id"]))

        if method == constants.LEADERBOARD_TYPE_RANK_WEIGHTED_WINS:
            ranking_list = self.get_rank_snapshot(slug)
            rankings = {}
            for r in ranking_list:
                rankings[r["user_id"]] = r["rank"]
            leaders = rank.rank_players_weighted(rankings, results_simple)
        elif method == constants.LEADERBOARD_TYPE_RANK_WINS:
            leaders = rank.rank_players_simple(results_simple)

        result = []
        pos = 1
        for lead in leaders:
            username = "Unknown"
            u = cache_user.get_user_by_id(lead[0])
            if u:
                username = u.get_user_name()
            row = {
                "rank": pos,
                "name": username,
                "wins": lead[1],
                "losses": lead[2],
                "games": lead[3],
            }
            if method == constants.LEADERBOARD_TYPE_RANK_WEIGHTED_WINS:
                row["weighted_wins"] = lead[4]
            result.append(row)
            pos += 1

        return result

    def get_rank_snapshot_date(self, group):
        for c in db.get_access_db():
            q = c.query(models_access.RankSnapshot)
            q = q.join(
                models_access.GroupAccess,
                models_access.RankSnapshot.group_id == models_access.GroupAccess.id,
            )
            q = q.filter(
                func.lower(models_access.GroupAccess.slug) == func.lower(group)
            )
            q = q.order_by(desc(models_access.RankSnapshot.time))
            q = q.limit(1)
            ret = q.first()
            if ret:
                return ret.time
        return None

    def get_rank_snapshot(self, group):
        rank_id = None
        for c in db.get_access_db():
            q = c.query(models_access.RankSnapshot)
            q = q.join(
                models_access.GroupAccess,
                models_access.RankSnapshot.group_id == models_access.GroupAccess.id,
            )
            q = q.filter(
                func.lower(models_access.GroupAccess.slug) == func.lower(group)
            )
            q = q.order_by(desc(models_access.RankSnapshot.time))
            q = q.limit(1)
            ret = q.first()
            if ret:
                rank_id = ret.id

        for c in db.get_access_db():
            q = c.query(models_access.RankSnapshotDetail)
            q = q.join(
                models_access.RankSnapshot,
                models_access.RankSnapshot.id
                == models_access.RankSnapshotDetail.rank_snapshot_id,
            )
            q = q.filter(models_access.RankSnapshotDetail.rank_snapshot_id == rank_id)

            ret = []
            for r in q.all():
                element = {"user_id": r.user_id, "rank": r.rank}
                u = cache_user.get_user_by_id(r.user_id)
                if u:
                    element["name"] = u.get_user_name()
                ret.append(element)

            value = len(ret)
            for r in ret:
                r["value"] = value
                value -= 1

            return ret

        return []

    def add_rank_snapshot(self, date, group, rankings):
        group_access = self.get_group_access(group)

        if group_access:
            ss_id = None
            for c in db.get_access_db():
                ss = models_access.RankSnapshot(time=date, group_id=group_access.id)
                c.add(ss)
                c.commit()
                ss_id = ss.id

            for c in db.get_access_db():
                rank = 1
                for r in rankings:
                    c.add(
                        models_access.RankSnapshotDetail(
                            rank_snapshot_id=ss_id, user_id=r, rank=rank
                        )
                    )
                    rank += 1
                c.commit()

            LOGGER.info(
                "Added Rank Snapshot for group {} with {} users".format(
                    group, len(rankings)
                )
            )
            return True

        return False

    def set_admin_user_access(
        self, source_user, username, login_type, login_status
    ) -> bool:
        if (
            constants.SYSTEM_USER == source_user
        ):  # db.get().check_user_role(source_user, constants.ROLE_ADMIN_WRITER):
            try:
                ua = self.get_user_access(username)

                for c in db.get_access_db():
                    if ua is None:
                        c.add(
                            models_access.UserAccess(
                                login_identifier=username,
                                login_type=login_type,
                                login_status=login_status,
                            )
                        )
                        LOGGER.info(
                            "Set User: Add NEW user: {}, {}, {}".format(
                                username, login_type, login_status
                            )
                        )
                    else:
                        ua_lookup = (
                            c.query(models_access.UserAccess)
                            .filter(models_access.UserAccess.id == ua.id)
                            .first()
                        )
                        ua_lookup.login_identifier = username
                        if login_type:
                            ua_lookup.login_type = login_type
                        if login_status is not None:
                            ua_lookup.login_status = login_status
                        c.flush()
                    c.commit()

                cache_user.invalidate_user(username)

                return True
            except Exception as ex:
                LOGGER.exception("Set Access Fail: ", exc_info=ex)
        else:
            LOGGER.error("Failed to auth user: " + source_user)
        return False
