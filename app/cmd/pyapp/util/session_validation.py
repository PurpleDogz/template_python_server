from . import custom_logging, roles, config
from fastapi_login.exceptions import InvalidCredentialsException

from fastapi import Request

from fastapi.security import SecurityScopes
from fastapi.responses import JSONResponse

import requests
import json


# import starlette.status as status

LOGGING_ID = "session_validation"
LOGGER = custom_logging.getLogger(LOGGING_ID)


class NotAuthenticatedException(Exception):
    pass


# these two argument are mandatory
def NotAuthenticatedExceptionMessage():
    return JSONResponse(
        status_code=401,
        content={"message": "Not Authenticated"},
    )


############################################
# Check the session key
class SessionValidation:
    def __init__(self, token_url: str, user_urls: list[str], use_cookie=True):
        self.token_url = token_url
        self.user_urls = user_urls
        self.use_cookie = use_cookie
        self._not_authenticated_exception = InvalidCredentialsException

    @property
    def not_authenticated_exception(self):
        """
        Exception raised when no (valid) token is present.
        Defaults to `fastapi_login.exceptions.InvalidCredentialsException`
        The property will deprecated in the future in favor of the custom_exception argument
        on initialization
        """
        return self._not_authenticated_exception

    @not_authenticated_exception.setter
    def not_authenticated_exception(self, value: Exception):
        """
        Setter for the Exception which raises when the user is not authenticated.
        Sets `self.auto_error` to False in order to raise the correct exception.

        Args:
            value (Exception): The Exception you want to raise
        """
        assert issubclass(value, Exception)  # noqa
        self._not_authenticated_exception = value

    async def __call__(self, request: Request, security_scopes: SecurityScopes = None):
        return {}

        try:
            role_list = (
                [roles.ROLE_ADMIN_READ_ONLY]
                if request.url.path not in self.user_urls
                else []
            )
            cookies = request.cookies
            token = (
                request.query_params["access"]
                if "access" in request.query_params.keys()
                else None
            )
            if token:
                cookies[config.get().get_cookie_name()] = token
            r = requests.post(
                self.token_url,
                data=json.dumps({"roles": role_list}),
                cookies=request.cookies,
            )
            if r and r.status_code == 200:
                return r.json()
            else:
                LOGGER.error(
                    "HTTP Error {}: Failed to auth request via: {}".format(
                        r.status_code, self.token_url
                    )
                )

        except Exception as ex:
            LOGGER.error(
                "Failed to auth request via: {} -> {}".format(self.token_url, str(ex))
            )
            pass

        # return NotAuthenticatedExceptionMessage()
        raise self.not_authenticated_exception

        return None

    async def optional(self, request: Request, security_scopes: SecurityScopes = None):
        """
        Acts as a dependency which catches all errors, i.e. `NotAuthenticatedException` and returns None instead
        """
        try:
            user = await self.__call__(request, security_scopes)
        except Exception:
            return None
        else:
            return user
