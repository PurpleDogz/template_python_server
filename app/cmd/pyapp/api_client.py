from typing import Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from urllib.parse import parse_qs
from http.cookies import SimpleCookie

from . import api_security, db, constants
from .util import (
    config,
    custom_logging,
    db_util,
    error_util,
    custom_log_api,
)

LOGGING_ID = "api_native"
LOGGER = custom_logging.getLogger(LOGGING_ID)

router = APIRouter(route_class=custom_log_api.LoggingRoute)


def get_router():
    return router


# Retrieve the session cookie
def get_request_cookie(request):
    cookie = SimpleCookie()
    cookie.load(request.headers.get("Cookie"))
    c_name = config.get().get_cookie_name()
    return {c_name: cookie[c_name].value}


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


##########################################


@router.post("/{group}/api/users")
async def group_users(
    request: Request, group: str, user=Depends(api_security.getLoginManager())
):
    if not db.get_access().get_user_access(user.get(api_security.KEY_USERNAME), group):
        return error_util.get_error_json(error_util.ERROR_FORBIDDEN)

    return db.get_access().get_group_users(group)


class GetLeaderboard(BaseModel):
    start_time: db_util.StrictDate = None
    end_time: db_util.StrictDate = None
    method: Optional[int] = None


@router.post("/{group}/api/leaderboard")
async def leaderboard(
    request: GetLeaderboard, group: str, user=Depends(api_security.getLoginManager())
):
    if not db.get_access().get_user_access(user.get(api_security.KEY_USERNAME), group):
        return error_util.get_error_json(error_util.ERROR_FORBIDDEN)

    method = constants.LEADERBOARD_TYPE_RANK_WINS
    if request.method:
        method = request.method

    return db.get_access().get_leaderboard(
        group, method, request.start_time, request.end_time
    )


@router.post("/{group}/api/rank_baseline")
async def rank_baseline(
    request: Request, group: str, user=Depends(api_security.getLoginManager())
):
    if not db.get_access().get_user_access(user.get(api_security.KEY_USERNAME), group):
        return error_util.get_error_json(error_util.ERROR_FORBIDDEN)

    dt = db.get_access().get_rank_snapshot_date(group)
    data = db.get_access().get_rank_snapshot(group)
    return {"update_date": dt, "results": data}


class GetHeadToHead(BaseModel):
    start_time: db_util.StrictDate = None
    end_time: db_util.StrictDate = None
    username: Optional[str] = None


@router.post("/{group}/api/head_to_head")
async def head_to_head(
    request: GetHeadToHead, group: str, user=Depends(api_security.getLoginManager())
):
    if not db.get_access().get_user_access(user.get(api_security.KEY_USERNAME), group):
        return error_util.get_error_json(error_util.ERROR_FORBIDDEN)

    username = user.get(api_security.KEY_USERNAME)
    if request.username:
        username = request.username

    return db.get_access().get_head_to_head(
        group, username, request.start_time, request.end_time
    )


class GetResults(BaseModel):
    start_date: db_util.StrictDate = None
    end_date: db_util.StrictDate = None
    search_comment: Optional[str] = None
    owner_only: Optional[bool] = None
    owner_filter: Optional[str] = None
    limit: Optional[int] = 1000


@router.post("/{group}/api/results")
async def results(
    request: GetResults, group: str, user=Depends(api_security.getLoginManager())
):
    if not db.get_access().get_user_access(user.get(api_security.KEY_USERNAME), group):
        return error_util.get_error_json(error_util.ERROR_FORBIDDEN)

    owner_filter = None
    if request.owner_filter:
        owner_filter = request.owner_filter
    elif request.owner_only is True:
        owner_filter = user.get(api_security.KEY_USERNAME)

    ret = db.get_access().get_rank_results(
        group,
        request.start_date,
        request.end_date,
        owner_filter,
        None,
        request.search_comment,
        True,
        request.limit,
    )

    if ret:
        return ret
    else:
        return []


class AddResult(BaseModel):
    date: db_util.StrictDate
    winner_id: int
    loser_id: int
    comment: str = None


@router.post("/{group}/api/result_add")
async def result_add(
    request: AddResult, group: str, user=Depends(api_security.getLoginManager())
):
    if db.get_access().add_result(
        user.get(api_security.KEY_USERNAME),
        group,
        request.date,
        request.winner_id,
        request.loser_id,
        request.comment,
    ):
        return error_util.get_success_json()
    else:
        return error_util.get_error_json(error_util.ERROR_FORBIDDEN)


class DeleteResult(BaseModel):
    id: int


@router.post("/{group}/api/result_delete")
async def result_delete(
    request: DeleteResult, group: str, user=Depends(api_security.getLoginManager())
):
    if db.get_access().delete_result(
        user.get(api_security.KEY_USERNAME), group, request.id
    ):
        return error_util.get_success_json()
    else:
        return error_util.get_error_json(error_util.ERROR_FORBIDDEN)


##########################################
# User Access

# @router.post("/admin_user_set")
# async def admin_user_set(request: Request, user=Depends(api_security.getSessionManager())):
#     j = await request.json()
#     return api_security.api_request("/set_user_access", get_request_cookie(request), j)
