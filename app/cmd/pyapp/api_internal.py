from fastapi import APIRouter, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .util import custom_logging, custom_log_api
from . import observability_helpers

LOGGING_ID = "api_internal"
LOGGER = custom_logging.getLogger(LOGGING_ID)

router = APIRouter(route_class=custom_log_api.LoggingRoute)

#############################################


def get_router():
    return router


def getLocalApp():
    l_app = FastAPI()
    l_app.logger = custom_logging.get(observability_helpers.get_logger_service())

    l_app.include_router(get_router())

    # TODO: Tighen origin?
    l_app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # logging.getLogger("uvicorn.access").handlers = []

    return l_app


app = getLocalApp()


def getApp() -> FastAPI:
    return app
