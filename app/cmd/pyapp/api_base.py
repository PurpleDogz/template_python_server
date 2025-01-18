import logging
import traceback

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from starlette.exceptions import HTTPException
from starlette.responses import FileResponse, RedirectResponse
from starlette.middleware.sessions import SessionMiddleware

from . import api_client, api_security, api_webui, api_web_base
from .util import config, custom_logging, observability_helpers

LOGGING_ID = "api_base"
LOGGER = custom_logging.getLogger(LOGGING_ID)


class AuthStaticFiles(StaticFiles):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

    async def __call__(self, scope, receive, send) -> None:
        assert scope["type"] == "http"

        valid_files = ["manifest.json", ".css", "/icons"]

        check_access = True

        for f in valid_files:
            if scope["path"].find(f) != -1:
                check_access = False
                break

        # Verify access to all non CSS
        if check_access:
            request = Request(scope, receive)
            # throws exception
            _ = await api_security.getLoginManager()(request)

        await super().__call__(scope, receive, send)


def getLocalApp():
    l_app = FastAPI()
    l_app.logger = custom_logging.get(observability_helpers.get_logger_service())

    l_app.include_router(api_web_base.get_router())
    l_app.include_router(api_webui.get_router(), prefix=config.get().APP_HOST_URL)
    l_app.include_router(api_client.get_router(), prefix=config.get().APP_HOST_URL)
    l_app.mount(
        config.get().APP_HOST_URL + "/static",
        StaticFiles(directory="pyapp/static"),
        name="static",
    )
    l_app.mount(
        config.get().APP_HOST_URL + "/js",
        AuthStaticFiles(directory="pyapp/js"),
        name="js",
    )

    # l_app.add_middleware(api_security.SecurityHeadersMiddleware, csp=False)

    # TODO: Tighen origin?
    l_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    if config.get().LOGIN_MODE == config.DEPLOYMENT_LOGIN_MODE_OAUTH:
        l_app.add_middleware(
            SessionMiddleware,
            secret_key=config.get().ACCESS_SECRET,
            max_age=config.get().ACCESS_TOKEN_EXPIRY_SECONDS,
            path=config.get().get_app_url(),
        )

    logging.getLogger("uvicorn.access").handlers = []

    return l_app


app = getLocalApp()

app.add_exception_handler(
    api_security.InvalidLoginException, api_security.InvalidLoginException_handler
)


@app.exception_handler(api_security.NotAuthenticatedException)
async def login_exception_handler(
    request: Request, exc: api_security.NotAuthenticatedException
):
    # Redirect the user to the login page or any other appropriate route
    return RedirectResponse(url="/")


# Define a route to handle OPTIONS requests for all endpoints
@app.options("/{path:path}")
def options_handler(request: Request, path: str):
    response_headers = {
        "Allow": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    return JSONResponse(status_code=200, headers=response_headers)


favicon_path = "pyapp/static/icons/favicon.ico"


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse(favicon_path)


# @app.get("/", include_in_schema=False)
# def home(request: Request, user=Depends(api_security.getUserManager())):
#     return RedirectResponse(url=config.get().get_app_url(), status_code=status.HTTP_302_FOUND)

##############################
# Auth Errors


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    # print(request.url)
    # print(request.method)
    # print(request.headers)
    # print(exc)
    # LOGGER.exception(
    #     "HTTP Exception: " + api_web.get_request_detail(request), exc_info = exc
    # )
    # parsed_url = urlparse(str(request.url))

    if api_security.isBrowserAgent(request):
        return RedirectResponse(
            url=config.get().get_app_url(), status_code=status.HTTP_302_FOUND
        )

    LOGGER.info(
        "HTTP Exception: "
        + api_webui.get_request_detail(request)
        + " Exec: "
        + "".join(traceback.format_exception_only(type(exc), exc)).strip()
    )

    return JSONResponse(status_code=401, content={"message": "Not Authenticated"})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    LOGGER.error(
        "Validation Exception: "
        + api_webui.get_request_detail(request)
        + " Exec: "
        + str(exc)
    )
    return RedirectResponse(
        url=config.get().get_app_url(), status_code=status.HTTP_302_FOUND
    )


def getApp() -> FastAPI:
    return app
