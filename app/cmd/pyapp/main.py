import logging
import uvicorn
import asyncio
import os
import signal
from uvicorn import Server
from types import FrameType
from typing import Optional

from . import db, api_base
from . import observability_helpers
from .util import config, custom_logging, key_killer

LOGGING_ID = "Main"
LOGGER = custom_logging.getLogger(LOGGING_ID)

logging.getLogger("passlib").setLevel(logging.ERROR)

###################################################
# Main


class APIServer(Server):
    async def run(self, sockets=None):
        self.config.setup_event_loop()
        # print("Start Server: " + str(self))
        return await self.serve(sockets=sockets)

    # Kill the entire process on the first interrupt
    def handle_exit(self, sig: int, frame: Optional[FrameType]) -> None:
        LOGGER.info("EXIT: Server Keypress Interupt Detected")
        # super().handle_exit(sig, frame)
        if key_killer.isWindows():
            os.kill(os.getpid(), signal.SIGINT)
        else:
            os.system("kill -9 {}".format(os.getpid()))
        # sys.exit()

    def add_done_callback(self, comp):
        # print("Server Stop: " + str(self))
        pass


async def run_servers(configList):
    apps = []
    for cfg in configList:
        server = APIServer(config=cfg)
        apps.append(server.run())
    return await asyncio.gather(*apps)


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Debug")
    parser.add_argument("-d", help="Debug trace", action="store_true")
    args = parser.parse_args()

    log_level = logging.INFO
    if args.d:
        log_level = logging.DEBUG

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s %(name)s:[%(levelname)s]: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )  # NOSONAR

    # Hide the health check
    class EndpointFilter(logging.Filter):
        def filter(self, record: logging.LogRecord) -> bool:
            return record.getMessage().find("/healthz") == -1

    if config.get().DEPLOYMENT_MODE == config.DEPLOYMENT_MODE_PRODUCTION:
        logging.getLogger("uvicorn.access").setLevel(logging.CRITICAL + 1)

    # Filter out /endpoint
    logging.getLogger("uvicorn.access").addFilter(EndpointFilter())
    logging.getLogger("gnsq.consumer").setLevel(logging.ERROR)

    # Always start, used for everything now
    custom_logging.get(observability_helpers.get_logger_service())
    if observability_helpers.get_logger_service() is None:
        print("Observability Service DISABLED")
    else:
        print("Observability Service ENABLED")

    LOGGER.info("Deployment Mode: " + config.get().DEPLOYMENT_MODE)
    LOGGER.info("Login Mode: " + config.get().LOGIN_MODE)
    if len(config.get().GOOGLE_CLIENT_ID) > 0:
        LOGGER.info("Google Client ID: " + config.get().GOOGLE_CLIENT_ID)

    # Init DB
    LOGGER.info("DB Connection: " + config.get().DB_HOST)

    db.get_access().init_db_defaults()

    # if config.get().ENABLE_EVENT_READERS == config.TRUE:
    #     service_log_reader.run()
    # else:
    #     LOGGER.info("Event Readers DISABLED")

    # service_daily.run()

    LOGGER.info(
        "WebServer: http://"
        + config.get().HOST_ADDRESS
        + ":"
        + str(config.get().PORT + config.get().APP_HOST_URL)
    )

    cfg1 = uvicorn.Config(
        api_base.getApp(),
        host=config.get().HOST_ADDRESS,
        port=int(config.get().PORT),
        lifespan="off",
        proxy_headers=True,
        forwarded_allow_ips="*",
        log_config=None,
    )

    # # Internal BFF API
    # cfg2 = uvicorn.Config(
    #     api_internal.getApp(),
    #     host="0.0.0.0",
    #     port=int(config.get().PORT_INTERNAL_API),
    #     lifespan="off",
    #     proxy_headers=True,
    #     forwarded_allow_ips="*",
    #     log_config=None,
    # )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_servers([cfg1]))
    # loop.run_until_complete(run_servers([cfg1, cfg2]))

    # server = uvicorn.Server(config=cfg)
    # server.run()


if __name__ == "__main__":
    main()
