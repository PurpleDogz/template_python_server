from .util import config, custom_logging
from .util import service_observability
import warnings

warnings.filterwarnings("ignore")

LOGGING_ID = "ObservabilityHelpers"
LOGGER = custom_logging.getLogger(LOGGING_ID)

##############################################
# Topics

###################################################
# Observability helper

# class IdentityTransformer(service_observability.ObTransformer):

#     async def process_item(self, topic, item):
#         if topic in [config.get().MESSAGE_TOPIC_REQUESTS] and isinstance(item,dict):
#             item['source_service'] = config.get().SERVICE_NAME
#         return item

###################################################
# Observability wrapper

_observability_service = None


def get_logger_service():
    if len(config.get().MESSAGE_SERVICE_HOST) == 0:
        return None
    global _observability_service
    if not _observability_service:
        async_transformers = []

        _observability_service = service_observability.ObservabilityServiceLogger(
            daemon=True,
            service_host=config.get().MESSAGE_SERVICE_HOST,
            async_transformers=async_transformers,
        )
        _observability_service.start()

    return _observability_service


def add_message(topic, data):
    get_logger_service().add_message({"topic": topic, "data": data})
