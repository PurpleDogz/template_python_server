from .util import custom_logging, service_base
import time

LOGGING_ID = "Daily"
LOGGER = custom_logging.getLogger(LOGGING_ID)


def run():
    t = Daily(daemon=True)
    t.start()


########################################################
# Service to run jobs daily

PURGE_DEFAULT_SLEEP = 60 * 60 * 24


class Daily(service_base.BaseService):
    def __init__(self, daemon=False):
        super().__init__(
            name=self.__class__,
            interval=PURGE_DEFAULT_SLEEP,
            logger=LOGGER,
            daemon=daemon,
        )

    def check(self):
        # Add delay to allow startup to complete on the main server.
        time.sleep(30)

        # Run Daily Jobs
