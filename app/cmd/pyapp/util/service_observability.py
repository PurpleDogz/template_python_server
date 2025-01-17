from . import service_base
from . import custom_logging
import json
import asyncio
import time
import gnsq
from queue import Empty, SimpleQueue
from abc import abstractmethod, ABC
import warnings

warnings.filterwarnings("ignore")

LOGGING_ID = "ObservabilityService"
LOGGER = custom_logging.getLogger(LOGGING_ID)

LOGGER_DEFAULT_SLEEP = 10

#########################################
# Transformaers


class ObTransformer(ABC):
    @abstractmethod
    async def process_item(self, topic, item):
        return item


#############################################
class ObservabilityServiceLogger(service_base.BaseService):
    def __init__(self, service_host, async_transformers=None, daemon=False):
        super().__init__(
            name=self.__class__,
            interval=LOGGER_DEFAULT_SLEEP,
            logger=LOGGER,
            daemon=daemon,
        )
        self.service_host = service_host
        self.async_transformers = async_transformers
        self._queue = SimpleQueue()

    def add_message(self, msg):
        self._queue.put(msg)

    def check(self):
        # Need to run in a new event loop as the interaction with the LoginManager is async
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self.run_loop())
        loop.close()

    async def run_loop(self):
        producer = None

        if len(self.service_host) > 0:
            LOGGER.info(
                "ObservabilityService: Connecting to GNSQ Service: {}".format(
                    self.service_host
                )
            )
            producer = gnsq.Producer(self.service_host)
            producer.start()

        # Batch items to deprioritise this work a bit..
        while True:
            commit_items = []
            # Grab all items available
            while True:
                try:
                    base_item = self._queue.get(block=False)
                    if base_item:
                        if (
                            "topic" not in base_item.keys()
                            or "data" not in base_item.keys()
                        ):
                            LOGGER.error(
                                "ObservabilityService: Invalid Message -> " + base_item
                            )
                            continue

                        topic = base_item["topic"]
                        item = base_item["data"]

                        if self.async_transformers:
                            for t in self.async_transformers:
                                if item:
                                    item = await t.process_item(topic, item)

                        if item:
                            commit_items.append((topic, item))
                    else:
                        break
                except Empty:
                    break
                except Exception as ex:
                    LOGGER.exception("ObservabilityService Error:", exc_info=ex)
                    break

            for item in commit_items:
                self.process_item(producer, item[0], item[1])

            time.sleep(LOGGER_DEFAULT_SLEEP)

    def process_item(self, producer, topic, data):
        if producer:
            try:
                msg = None
                if isinstance(data, dict):
                    msg = json.dumps(data).encode("utf-8")
                elif isinstance(data, str):
                    msg = data.encode("utf-8")
                if msg:
                    producer.publish(topic, msg)
                    # LOGGER.info("ObservabilityService: Message Sent: Topic: {}, Data: {}".format(topic, str(msg)))
                else:
                    LOGGER.info(
                        "ObservabilityService: Message Skipped (not dict or str): Topic: {}, Data: {}".format(
                            topic, str(msg)
                        )
                    )
            except gnsq.errors.NSQException:
                # LOGGER.info("ObservabilityService Message Q Disconnected")
                pass
            except gnsq.errors.NSQSocketError:
                # LOGGER.info("ObservabilityService Message Q Disconnected")
                pass
            except ConnectionAbortedError:
                # LOGGER.info("ObservabilityService Message Q Disconnected")
                pass
            except Exception as ex:
                # LOGGER.exception("ObservabilityService Error:", exc_info=ex)
                LOGGER.info("ObservabilityService Error:" + str(ex))
                pass
