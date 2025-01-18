import os
import json
from datetime import datetime

from authlib.integrations.starlette_client import OAuthError
from fastapi import APIRouter, Request, status, Depends
from fastapi.responses import RedirectResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.templating import Jinja2Templates

# import starlette.status as status
from . import api_security
from .util import config, custom_logging, theme, security, db_util
from . import db, constants, cache_session, cache_user

LOGGING_ID = "api_webui"
LOGGER = custom_logging.getLogger(LOGGING_ID)

##############################
# Misc

folder = os.path.dirname(__file__)
template_folder = os.path.join(folder, "templates")
template_folder = os.path.abspath(template_folder)
templates = Jinja2Templates(directory=template_folder)


def isMobileAgent(request):
    if (
        "mobile" in request.query_params.keys()
        and request.query_params["mobile"] == "true"
    ):
        return True
    try:
        from user_agents import parse

        user_agent = parse(request.headers.get("user-agent"))
        return user_agent.is_mobile or user_agent.is_tablet
    except Exception:
        return False
        pass

def isEmbedded(request):
    try:
        if request.cookies.get("embedded") == "true":
            return True
    except Exception:
        pass

    if "embedded" in request.query_params.keys():
        return True

    return False


def getDefaultArgs(request, group, username, addArgs=None):
    g = db.get_access().get_group_access(group)

    args = {
        "now": config.get().get_startup_ts(),
        "request": request,
        "app_url": config.get().APP_HOST_URL,
        "theme": theme.get(),
        "username_full": username,
        "username_formatted": cache_user.UserCacheOb.format_user(username),
        "title": g.name if g else "Default",
        "icon_name": g.icon if g else config.get().ICON_NAME,
        "mobile": isMobileAgent(request),
    }

    if isEmbedded(request):
        args["embedded"] = True
        args["mobile"] = True

    if addArgs:
        args = args | addArgs

    return args


def get_request_detail(r):
    sourceIP = r.client.host
    if "x-real-ip" in r.headers.keys():
        sourceIP = r.headers["x-real-ip"]
    ret = "SRC: {} REQ: {} {}".format(sourceIP, r.method, r.url.path)
    if len(r.query_params.keys()) > 0:
        ret += "?{}".format(r.query_params)
    return ret


def formatHTML(request, page):
    # if isMobileAgent(request):
    #     return page + "_mobile.html"
    return page + ".html"


def addParam(request, args, param):
    args[param] = (
        request.query_params[param] if param in request.query_params.keys() else ""
    )


app = APIRouter()


def get_router():
    return app


##############################
# Misc

favicon_path = "pyapp/static/icons/favicon.ico"

@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


##############################
# Core

@app.get("/", include_in_schema=False)
async def login(request: Request, include_in_schema=False):
    groups = db.get_access().get_all_groups()

    return templates.TemplateResponse(
        "login_select.html",
        {
            "request": request,
            "theme": theme.get(),
            "groups": groups,
            "app_url": config.get().APP_HOST_URL,
        },
    )

@app.get("/{group}/results", include_in_schema=False)
def results(request: Request, group: str, user=Depends(api_security.getLoginManager())):
    u = db.get_access().get_user_access(user.get(api_security.KEY_USERNAME), group)
    if u:
        g = db.get_access().get_group_access(group)
        args = {"slug": g.slug, "group": g.name}
        addParam(request, args, "search_comment")
        args["user_id"] = u.id
        return templates.TemplateResponse(
            formatHTML(request, "results"),
            getDefaultArgs(request, group, user.get(api_security.KEY_USERNAME), args),
        )

    return RedirectResponse(
        url=config.get().APP_HOST_URL + "/login_fail?reason=Access Denied",
        status_code=status.HTTP_302_FOUND,
    )

@app.get("/{group}/login", include_in_schema=False)
async def login_context(request: Request, group: str, include_in_schema=False):
    ga = db.get_access().get_group_access(group)
    if not ga:
        return RedirectResponse(
            url=config.get().APP_HOST_URL + "/login_fail?reason=Access Denied",
            status_code=status.HTTP_302_FOUND,
        )

    return templates.TemplateResponse(
        "login.html",
        {
            "request": request,
            "slug": ga.slug,
            "group": ga.name,
            "theme": theme.get(),
            "app_url": config.get().APP_HOST_URL,
            "login_mode": config.get().LOGIN_MODE,
        },
    )


@app.get("/login_fail", include_in_schema=False)
async def login_fail(request: Request, include_in_schema=False):
    LOGGER.error("Login Fail Exception: " + api_security.get_request_detail(request))
    return templates.TemplateResponse(
        "login_fail.html", getDefaultArgs(request, "", "", dict(request.query_params))
    )


# Basic Auth -> Form Post
@app.post("/{group}/auth/token", include_in_schema=False)
async def auth_token(
    request: Request, group: str, data: OAuth2PasswordRequestForm = Depends()
):
    access_granted = False

    if db.get_access().check_user_login_access(
        data.username, constants.LOGIN_MODE_BASIC_AUTH
    ):
        user = api_security.load_user_by_key(data.username)
        if user and security.verify_password(
            data.password, user.get(api_security.KEY_PASSWORD_HASHED)
        ):
            access_granted = True

    if access_granted:
        # Access Granted
        session_id = cache_session.get().allocate_session_id(data.username)
        access_token = api_security.createAccessToken(data.username, session_id)

        msg = "Success via Form Submit"

        url = config.get().get_app_url() + group + "/leaderboard"

        response = RedirectResponse(url=url, status_code=status.HTTP_302_FOUND)
        api_security.setAuthCookie(response, access_token)

        cache_session.get().set_session(
            session_id,
            access_token,
            data.username,
            "Browser",
            "1.0",
            "0",
            api_security.getIP(request),
            meta=json.dumps({"msg": msg}),
        )
        # observability_helpers.capture_login_event(
        #     user.get(api_security.KEY_USERNAME),
        #     observability_helpers.JH_EVENT_LOGIN,
        #     msg,
        #     { "IP" : api_security.getIP(request) }
        # )

        LOGGER.info(
            "LOGIN: Basic Auth -> SUCCESS [Username: {}, IP: {}]".format(
                data.username, api_security.getIP(request)
            )
        )

        return response

    # observability_helpers.capture_login_event(
    #     data.username,
    #     observability_helpers.JH_EVENT_LOGIN_FAIL,
    #     "Form Post",
    #     { "IP" : api_security.getIP(request) }
    # )

    LOGGER.info(
        "LOGIN: Basic Auth -> FAIL [Username: {}, IP: {}]".format(
            data.username, api_security.getIP(request)
        )
    )

    return RedirectResponse(
        url=config.get().APP_HOST_URL + "/login_fail?reason=Access Denied",
        status_code=status.HTTP_302_FOUND,
    )


@app.get("/logout", include_in_schema=False)
async def route_logout_and_remove_cookie(
    request: Request, user=Depends(api_security.getLoginManager())
):
    response = RedirectResponse(url=config.get().get_app_url())
    api_security.getLoginManager().set_cookie(response, "")
    if config.get().LOGIN_MODE == constants.LOGIN_MODE_OAUTH:
        request.session.pop("user", None)

    response.set_cookie(key=config.COOKIE_GROUP, value="")

    session_id = user.get(api_security.KEY_SESSION_ID)
    if session_id:
        cache_session.get().remove_session_by_id(session_id)

    # observability_helpers.capture_login_event(
    #     user.get(api_security.KEY_USERNAME), observability_helpers.JH_EVENT_LOGOFF, "Success", { "IP" : api_security.getIP(request) }
    # )
    # response.delete_cookie("Authorization", domain="localtest.me")
    return response


# 3rd Party OAuth
@app.get("/{group}/login_google", include_in_schema=False)
async def login_google(request: Request, group: str):
    redirect_uri = request.url_for("auth_google")
    if config.get().GOOGLE_FORCE_HTTPS_REDIRECT == config.TRUE:
        redirect_uri = str(redirect_uri).lower().replace("http:", "https:")

    # redirect_uri += "?group=" + group

    LOGGER.info("Google Auth: Redirect URL: " + str(redirect_uri))

    return await api_security.getOAuthManager().google.authorize_redirect(
        request, str(redirect_uri)
    )


@app.get("/auth_google", include_in_schema=False)
async def auth_google(request: Request):
    LOGGER.info(
        "Google Auth: Response: URL:{}, PARAMS:{}".format(
            request.url, str(request.path_params)
        )
    )

    try:
        token = await api_security.getOAuthManager().google.authorize_access_token(
            request
        )
    except OAuthError as error:
        LOGGER.error("Google Auth: Failed -> " + str(error))
        return RedirectResponse(
            url=config.get().APP_HOST_URL + "/login_fail?reason=" + error.error,
            status_code=status.HTTP_302_FOUND,
        )

    return handle_auth_response(token, constants.LOGIN_MODE_GOOGLE, request)


def handle_auth_response(token: str, login_type: str, request: Request):
    access_token, user_info, error = api_security.validate_token(
        token, login_type, request
    )

    redirect_url = config.get().get_app_url()

    group = request.cookies.get(config.COOKIE_GROUP)
    if group and len(group) > 0:
        redirect_url += group + "/"
    else:
        try:
            # Just resolve to first group for now.
            group_access = db.get_access().get_user_access_groups(user_info["email"])
            if len(group_access) > 0:
                redirect_url += group_access[0].slug + "/"
        except Exception:
            pass

    response = RedirectResponse(url=redirect_url, status_code=status.HTTP_302_FOUND)

    if access_token:
        api_security.setAuthCookie(response, access_token)
        request.session["user"] = user_info
    else:
        LOGGER.error("Login Failed: Failed to create access token")

    if error:
        return RedirectResponse(
            url=config.get().APP_HOST_URL + "/login_fail?reason=" + error,
            status_code=status.HTTP_302_FOUND,
        )

    return response


@app.get("/terms", include_in_schema=False)
async def terms(request: Request, include_in_schema=False):
    return templates.TemplateResponse("terms.html", getDefaultArgs(request, "", ""))


@app.get("/privacy", include_in_schema=False)
async def privacy(request: Request, include_in_schema=False):
    return templates.TemplateResponse("privacy.html", getDefaultArgs(request, "", ""))
