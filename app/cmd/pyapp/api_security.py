import logging
from collections import OrderedDict
from datetime import timedelta, timezone
from authlib.integrations.starlette_client import OAuth
from fastapi import (
    FastAPI,
    Request,
    Response,
)
from fastapi_login import LoginManager
from starlette.config import Config
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import RedirectResponse
from datetime import datetime
import json
import requests
import jwt

from . import db, constants, cache_session
from .util import config

# import starlette.status as status

LOGGING_ID = "api_security"
LOGGER = logging.getLogger(LOGGING_ID)

KEY_USERID = "user_id"
KEY_USERNAME = "username"
KEY_PASSWORD = "password"
KEY_PASSWORD_HASHED = "password_hashed"
KEY_SESSION_ID = "session_id"

FIELD_REMOVE_ATHLETE = [KEY_PASSWORD_HASHED]

##################################
# General


def get_request_detail(r):
    sourceIP = r.client.host
    if "x-real-ip" in r.headers.keys():
        sourceIP = r.headers["x-real-ip"]
    ret = "SRC: {} REQ: {} {}".format(sourceIP, r.method, r.url.path)
    if len(r.query_params.keys()) > 0:
        ret += "?{}".format(r.query_params)
    return ret


def getIP(request: Request):
    source = ""
    try:
        source = request.client.host
        header = dict(request.headers)
        if "x-real-ip" in header.keys():
            source = header["x-real-ip"]
    except Exception as ex:
        LOGGER.error("Failed to get IP: {}".format(str(ex)))
        pass
    return source


def isBrowserAgent(request):
    user_agent = request.headers.get("User-Agent")

    if user_agent:
        if "Mozilla" in user_agent:
            # Check for "Mozilla" in the user agent string
            return True

    return False


def isMobileAgent(request):
    try:
        if (
            "mobile" in request.query_params.keys()
            and request.query_params["mobile"] == "true"
        ):
            return True
        if (
            "embedded" in request.query_params.keys()
            and request.query_params["embedded"] == "true"
        ):
            return True
        from user_agents import parse

        user_agent = parse(request.headers.get("user-agent"))
        return user_agent.is_mobile or user_agent.is_tablet
    except Exception:
        return False
        pass


class InvalidLoginException(Exception):
    pass


# these two argument are mandatory
def InvalidLoginException_handler(request, exc):
    return RedirectResponse(url=config.get().APP_HOST_URL + "/")


class NotAuthenticatedException(Exception):
    pass


# these two argument are mandatory
def NotAuthenticatedException_handler(request, exc):
    # return JSONResponse(
    #     status_code=401,
    #     content={"message": "Not Authenticated"},
    # )

    # return error.get_error_json(error.ERROR_AUTH)
    return RedirectResponse(url="/")


class CustomLoginManager(LoginManager):
    def __init__(
        self,
        secret: any,
        token_url: str,
        use_cookie: bool,
        use_header: bool,
        not_authenticated_exception: any,
        default_expiry: timedelta,
        cookie_name: str,
    ):
        super().__init__(
            secret=secret,
            token_url=token_url,
            use_cookie=use_cookie,
            use_header=use_header,
            default_expiry=default_expiry,
            not_authenticated_exception=not_authenticated_exception,
            cookie_name=cookie_name,
        )

    # Overide to looks in the params and set the search order:
    # params > headers > cookies
    # * this is due to axios sending stale cookies in the request from RN, seems hard to override on the client side
    async def _get_token(self, request: Request):
        token = (
            request.query_params["access"]
            if "access" in request.query_params.keys()
            else None
        )

        if token:
            return token

            # Tries to grab the token from the header
        if token is None and self.use_header:
            token = await super(LoginManager, self).__call__(request)

        if token:
            return token

        try:
            if self.use_cookie:
                token = self._token_from_cookie(request)
        # The Exception is either a InvalidCredentialsException
        # or a custom exception set by the user
        except Exception as _e:
            # In case use_cookie and use_header is enabled
            # headers should be checked if cookie lookup fails
            if self.use_header:
                pass
            else:
                raise self.not_authenticated_exception  # noqa: B904

        return token


manager = CustomLoginManager(
    config.get().ACCESS_SECRET,
    token_url="/auth/token",
    use_cookie=True,
    use_header=True,
    default_expiry=timedelta(seconds=config.get().ACCESS_TOKEN_EXPIRY_SECONDS),
    not_authenticated_exception=NotAuthenticatedException(),
    cookie_name=config.get().get_cookie_name(),
)


def load_user_by_key(username: str):
    user = None
    a = db.get_access().get_user_access(username)
    if a:
        user = {
            KEY_USERID: a.id,
            KEY_USERNAME: a.login_identifier,
            KEY_PASSWORD_HASHED: a.password_hashed,
        }
    return user


@manager.user_loader()
def load_user(user_data: dict):  # could also be an asynchronous function
    user = load_user_by_key(str(user_data.get(KEY_USERNAME)))
    # Add the session ID into the user data
    if user:
        session_id = user_data.get(KEY_SESSION_ID)
        if session_id:
            user[KEY_SESSION_ID] = session_id
    return user


def getLoginManager():
    return manager


# Create an access token for the user
def createAccessToken(username, session_id):
    return getLoginManager().create_access_token(
        data=dict(sub={KEY_USERNAME: username, KEY_SESSION_ID: session_id})
    )


# Lock down the cookie to max security
def setAuthCookie(response, access_token):
    response.set_cookie(
        key=getLoginManager().cookie_name,
        value=access_token,
        httponly=True,
        max_age=config.get().ACCESS_TOKEN_EXPIRY_SECONDS,
        secure=(
            True
            if config.get().DEPLOYMENT_MODE == config.DEPLOYMENT_MODE_PRODUCTION
            else False
        ),
        # Image URL fails without the 'None", but non HTTPS mode needs "Lax" to allow the login cookie to be set, for now set devel to lax, research later.
        samesite="None"
        if config.get().DEPLOYMENT_MODE == config.DEPLOYMENT_MODE_PRODUCTION
        else "Lax",
    )


##################################
# Core Token Validation
# This is used to validate a tokens linked user and allocate access based on operating mode


def validate_token(token, login_type=None, request=None):
    if token:
        user = token.get("userinfo")
        if user:
            LOGGER.debug("Login: Extract user info: {}".format(user))

            user_info = dict(user)
            username = (
                user_info["email"].lower() if "email" in user_info.keys() else None
            )

            # Validate the user has access
            if username:
                if not config.get().check_email_domain(username):
                    LOGGER.error("Login: Email Domain Rejected: {}".format(username))
                    return None, None, "Email Domain Disabled"

                found = db.get_access().check_user_login_access(username, login_type)
                # OPEN
                if not found:
                    ua = db.get_access().get_user_access(username)
                    # Check if not explicitly disabled
                    if ua:
                        if ua.login_status == constants.LOGIN_STATUS_DISABLED:
                            return None, None, "Account Disabled"
                    # New Account
                    default_login_status = constants.LOGIN_STATUS_NON_SUBSCRIBER
                    db.get_access().set_admin_user_access(
                        constants.SYSTEM_USER,
                        username,
                        login_type,
                        default_login_status,
                    )
                    if request:
                        group = request.cookies.get(config.COOKIE_GROUP)
                        if group and len(group) > 0:
                            db.get_access().set_user_group(username, group)

            else:  # Fail
                LOGGER.error("Login: Empty Email User: {}".format(str(user)))
                return None, None, "Access Denied"

            # Allocate a session id and token
            session_id = cache_session.get().allocate_session_id(username)
            access_token = createAccessToken(username, session_id)

            if access_token:
                LOGGER.info("Login: Access token create for user: {}".format(username))
                msg = "Success via OAuth (Desktop)"
                if request and isMobileAgent(request):
                    msg = "Success via OAuth (Mobile)"
                # observability_helpers.capture_login_event(username, observability_helpers.JH_EVENT_LOGIN, msg, { "IP" : getIP(request) if request else "None" })
                cache_session.get().set_session(
                    session_id, access_token, username, meta=json.dumps({"msg": msg})
                )
            else:
                LOGGER.error(
                    "Login: Failed to create access token for user: {}".format(username)
                )

            return access_token, user_info, None
        else:
            LOGGER.error("Login: Failed to extract user info from: {}".format(token))
    else:
        LOGGER.error("Login Failed: Token is empty")

    return None, None, "Token Creation Failed"


##########################################
# Refresh Token


def create_refresh_token(secret, username, expire_seconds):
    to_encode = {}
    expiry = datetime.now(timezone.utc) + timedelta(seconds=expire_seconds)
    to_encode.update({"expiry": expiry.isoformat()})
    to_encode.update({"username": username})

    return jwt.encode(to_encode, secret, "HS256")


# Validate that the refresh token is alive and refers to the access token
def verify_token(secret: str, token: str, username: str):
    try:
        payload = jwt.decode(token, secret, "HS256")
        # From loginmanager
        token_username = payload.get("sub")
        if token_username is None or token_username != username:
            return False
    except Exception as ex:
        LOGGER.error("Login: Failed to decode token: {}".format(token), exc_info=ex)
        return False

    return True


# Validate that the refresh token is alive and refers to the access token
def verify_refresh_token(secret: str, token: str, username: str):
    try:
        payload = jwt.decode(token, secret, "HS256")
        exp = payload.get("expiry")
        if exp is None or datetime.fromisoformat(exp) < datetime.now(timezone.utc):
            return False
        token_username = payload.get("username")
        if token_username is None or token_username != username:
            return False
    except Exception as ex:
        LOGGER.error(
            "Login: Failed to decode refresh token: {}".format(token), exc_info=ex
        )
        return False

    return True


# Build the response with the refresh token
def build_token_response(username: str, access_token: str, resp: dict):
    refresh_token = create_refresh_token(
        config.get().ACCESS_SECRET, username, config.get().ACCESS_TOKEN_EXPIRY_SECONDS
    )
    expiry = datetime.now(timezone.utc) + timedelta(
        seconds=config.get().ACCESS_TOKEN_EXPIRY_SECONDS
    )
    data = {
        "access_token": access_token,
        "token_type": "bearer",
        "refresh_token": refresh_token,
        "expiry": expiry.isoformat(),
    }
    return {**resp, **data}


########################################################
def verify_google_token(token):
    try:
        response = requests.get(
            f"https://www.googleapis.com/oauth2/v3/tokeninfo?access_token={token}"
        )
        response.raise_for_status()
        data = response.json()
        email = data.get("email")
        return email
    except requests.exceptions.RequestException as ex:
        LOGGER.error("Login: Failed to verify google token: {}".format(str(ex)))
        pass

    return None


##################################
# Google Auth

oauth_starlette_config = Config(
    environ={
        "GOOGLE_CLIENT_ID": config.get().GOOGLE_CLIENT_ID,
        "GOOGLE_CLIENT_SECRET": config.get().GOOGLE_CLIENT_SECRET,
    }
)


class DictCache(dict):
    async def set(self, k, v, timeout=None):
        self[k] = v

    async def get(self, k):
        if k in self.keys():
            return self[k]
        return None

    async def delete(self, k):
        pass
        # self.pop(k, None)

    def __bool__(self):
        return True


# oauth = OAuth(oauth_starlette_config, cache=DictCache())
oauth = OAuth(oauth_starlette_config)

oauth.register(
    name="google",
    server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
    client_kwargs={"scope": "openid email profile"},
)


def getOAuthManager():
    return oauth


##################################
# Apple Auth

# import os
# from starlette.applications import Starlette
# from starlette.responses import RedirectResponse
# from starlette.middleware.sessions import SessionMiddleware
# from authlib.integrations.starlette_client import OAuth2Session

# # Set up the OAuth2Session for Apple
# APPLE_CLIENT_ID = os.environ.get('APPLE_CLIENT_ID')
# APPLE_CLIENT_SECRET = os.environ.get('APPLE_CLIENT_SECRET')
# APPLE_REDIRECT_URI = 'http://localhost:8000/auth/callback'
# APPLE_SCOPE = 'email name'
# APPLE_AUTH_URL = 'https://appleid.apple.com/auth/authorize'
# APPLE_TOKEN_URL = 'https://appleid.apple.com/auth/token'
# APPLE_API_BASE_URL = 'https://api.apple.com'

# oauth = OAuth2Session(
#     client_id=APPLE_CLIENT_ID,
#     client_secret=APPLE_CLIENT_SECRET,
#     redirect_uri=APPLE_REDIRECT_URI,
#     scope=APPLE_SCOPE,
#     authorization_endpoint=APPLE_AUTH_URL,
#     token_endpoint=APPLE_TOKEN_URL,
#     api_base_url=APPLE_API_BASE_URL,
# )

# # Set up the Starlette app
# app = Starlette()
# app.add_middleware(SessionMiddleware, secret_key=os.environ.get('SESSION_SECRET'))

# # Route for initiating the OAuth flow
# @app.route('/auth')
# async def auth(request):
#     authorization_url, state = oauth.create_authorization_url(APPLE_AUTH_URL)
#     request.session['oauth_state'] = state
#     return RedirectResponse(authorization_url)

# # Callback route for handling the response from Apple
# @app.route('/auth/callback')
# async def auth_callback(request):
#     token = await oauth.fetch_token(APPLE_TOKEN_URL, authorization_response=request.url, state=request.session['oauth_state'])
#     # Use the token to make API requests to Apple
#     # For example, you can get the user's email address:
#     user_info = await oauth.get('https://api.apple.com/auth/userinfo')
#     email = user_info.json()['email']
#     return {'email': email}

# if __name__ == '__main__':
#     import uvicorn
#     uvicorn.run(app, host='localhost', port=8000)

##################################
# HTTP Headers

CSP: dict[str, str | list[str]] = {
    "default-src": "'self'",
    "img-src": [
        "*",
        # For SWAGGER UI
        "data:",
    ],
    "connect-src": "'self'",
    "script-src": "'self'",
    "style-src": ["'self'", "'unsafe-inline'"],
    "script-src-elem": [
        # For SWAGGER UI
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui-bundle.js",
        "'sha256-1I8qOd6RIfaPInCv8Ivv4j+J0C6d7I8+th40S5U/TVc='",
    ],
    "style-src-elem": [
        # For SWAGGER UI
        "https://cdn.jsdelivr.net/npm/swagger-ui-dist@4/swagger-ui.css",
    ],
}


def parse_policy(policy: dict[str, str | list[str]] | str) -> str:
    """Parse a given policy dict to string."""
    if isinstance(policy, str):
        # parse the string into a policy dict
        policy_string = policy
        policy = OrderedDict()

        for policy_part in policy_string.split(";"):
            policy_parts = policy_part.strip().split(" ")
            policy[policy_parts[0]] = " ".join(policy_parts[1:])

    policies = []
    for section, content in policy.items():
        if not isinstance(content, str):
            content = " ".join(content)
        policy_part = f"{section} {content}"

        policies.append(policy_part)

    parsed_policy = "; ".join(policies)

    return parsed_policy


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses."""

    def __init__(self, app: FastAPI, csp: bool = True) -> None:
        """Init SecurityHeadersMiddleware.

        :param app: FastAPI instance
        :param no_csp: If no CSP should be used;
            defaults to :py:obj:`False`
        """
        super().__init__(app)
        self.csp = csp

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        """Dispatch of the middleware.

        :param request: Incoming request
        :param call_next: Function to process the request
        :return: Return response coming from from processed request
        """
        headers = {
            "Content-Security-Policy": "" if not self.csp else parse_policy(CSP),
            "Cross-Origin-Opener-Policy": "same-origin",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Strict-Transport-Security": "max-age=31556926; includeSubDomains",
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
        }
        response = await call_next(request)
        response.headers.update(headers)

        return response

    # app.add_middleware(SecurityHeadersMiddleware, csp=True)
