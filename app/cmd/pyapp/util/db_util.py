import json
import os

from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import DeclarativeMeta
from datetime import date, datetime, timezone
from pydantic.datetime_parse import parse_date
from typing import Any
from urllib.parse import parse_qs

try:
    from . import config
except Exception:
    import config

class AlchemyEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj.__class__, DeclarativeMeta):
            # an SQLAlchemy class
            fields = {}
            for field in [
                x for x in dir(obj) if not x.startswith("_") and x != "metadata"
            ]:
                data = obj.__getattribute__(field)
                handled = False
                # Handle dt
                try:
                    dt_obj = datetime.strptime(str(data), "%Y-%m-%d %H:%M:%S")
                    fields[field] = dt_obj.strftime("%Y-%m-%d %H:%M:%S")
                    handled = True
                except Exception:
                    pass
                if handled is False:
                    try:
                        json.dumps(
                            data, allow_nan=False
                        )  # this will fail on non-encodable values, like other classes
                        fields[field] = data
                    except Exception:
                        fields[field] = None
            # a json-encodable dict
            return fields

        return json.JSONEncoder.default(self, obj)


def jsonLoad(obj, fieldsRemove):
    j = json.loads(json.dumps(obj, cls=AlchemyEncoder))

    keys_to_remove = set(fieldsRemove).intersection(set(j.keys()))
    for key in keys_to_remove:
        del j[key]

    # Remove Empty also
    j = remove_empty_elements(j)

    return j


def remove_empty_elements(d):
    """recursively remove empty lists, empty dicts, or None elements from a dictionary"""

    def empty(x):
        return x is None or x == {} or x == []

    if not isinstance(d, (dict, list)):
        return d
    elif isinstance(d, list):
        return [v for v in (remove_empty_elements(v) for v in d) if not empty(v)]
    else:
        return {
            k: v
            for k, v in ((k, remove_empty_elements(v)) for k, v in d.items())
            if not empty(v)
        }


def init_engine(mode, folder, host, db, username, password):
    if mode == config.DB_MODE_SQLITE:
        check_dir_exists(folder)
        return create_engine(
            "sqlite:///{}/{}.db".format(folder, db),
            connect_args={"check_same_thread": False},
        )
    if mode == config.DB_MODE_POSTGRESQL:
        return create_engine(
            "postgresql://{}:{}@{}/{}".format(username, password, host, db)
        )


#############################################
## Misc function here for now


def check_dir_exists(dir):
    try:
        os.stat(dir)
    except Exception:
        os.mkdir(dir)


def extract_string(s, first, second):
    start = s.find(first)
    if second is None:
        return s[start + 1 :]
    end = s.find(second, start)
    return s[start + 1 : end]


class utc_datetime(datetime):
    @classmethod
    def __get_validators__(cls):
        yield cls.ensure_tzinfo

    @classmethod
    def ensure_tzinfo(cls, v):
        v1 = v

        if isinstance(v, str):
            v1 = datetime.strptime(v, "%Y-%m-%dT%H:%M:%S.%fZ")

        # if TZ isn't provided, we assume UTC, but you can do w/e you need
        if v1.tzinfo is None:
            return v1.replace(tzinfo=timezone.utc)
        # else we convert to utc
        return v1.astimezone(timezone.utc)

    @staticmethod
    def to_str(dt: datetime) -> str:
        return dt.isoformat()  # replace with w/e format you want

    # Simple Date


def validate_date(v: Any) -> date:
    return parse_date(v)


class StrictDate(date):
    @classmethod
    def __get_validators__(cls):
        yield validate_date


def get_params(j):
    data = parse_qs(j.decode("utf-8"))

    parameters = {}
    for param in data.keys():
        e = data[param]
        if isinstance(e, list) and len(e) > 0:
            parameters[param] = str(e[0])
        else:
            parameters[param] = str(e)

    return parameters
