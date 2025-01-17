from .util import custom_logging, config, service_q_reader
from . import db

LOGGING_ID = "LogReader"
LOGGER = custom_logging.getLogger(LOGGING_ID)

###################################################
# Service


def run():
    t = LogReader(daemon=True)
    t.start()


class LogReader(service_q_reader.QReader):
    def __init__(
        self,
        daemon=False,
    ):
        super().__init__(
            topic=config.get().MESSAGE_TOPIC_LOG,
            channel=config.get().SERVICE_NAME,
            host=config.get().MESSAGE_SERVICE_HOST,
            daemon=daemon,
            logger=LOGGER,
        )

    def process_message(self, msg):
        db.get_observability().add_log_event(msg)
