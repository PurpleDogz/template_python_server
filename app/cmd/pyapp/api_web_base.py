from fastapi import APIRouter

from .util import custom_logging

LOGGING_ID = "api_web_base"
LOGGER = custom_logging.getLogger(LOGGING_ID)

app = APIRouter()


def get_router():
    return app


##############################
# Misc


@app.get("/healthz", include_in_schema=False)
async def healthz():
    return {"status": 200}
