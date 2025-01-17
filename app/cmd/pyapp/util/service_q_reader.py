import ansq
import json
import asyncio

from . import custom_logging, service_base

LOGGING_ID = "BaseQReader"
LOGGER = custom_logging.getLogger(LOGGING_ID)

###################################################
# Service


class QReader(service_base.BaseService):
    def __init__(self, topic, channel, host, daemon=False, logger=None):
        self.topic = topic
        self.channel = channel
        self.host = host
        if not logger:
            logger = LOGGER
        super().__init__(name=self.__class__, daemon=daemon, logger=logger)

    def check(self):
        asyncio.run(self.do_check())

    async def do_check(self):
        self.logger.info(
            "Connecting to Message Bus [Topic: {}, Consumer: {}, Service: {}]".format(
                self.topic, self.channel, self.host
            )
        )

        def handler(message):
            try:
                msg = json.loads(message.body)
                self.process_message(msg)
            except Exception as ex:
                self.logger.exception(
                    "{} : Failed to process message -> {}".format(self.name, str(ex)),
                    exc_info=ex,
                )
                pass

        try:
            reader = await ansq.create_reader(
                topic=self.topic, channel=self.channel, nsqd_tcp_addresses=[self.host]
            )

            async for message in reader.messages():
                handler(message)
                await message.fin()

            await reader.close()
        except ConnectionRefusedError:
            self.logger.exception(
                "{} : Q Reader Failed to Connect -> {}".format(self.name, self.host)
            )
            pass
        except Exception as ex:
            self.logger.exception(
                "{} : Q Reader Error -> {}".format(self.name, str(ex))
            )  # , exc_info=ex)
            pass

        self.logger.info(
            "Consumer Close [Topic: {}, Consumer: {}, Service: {}]".format(
                self.topic, self.channel, self.host
            )
        )


# def process_message(msg):
#     source = msg['source']
#     source_type = msg['source_type']
# db.get_observability().add_metrics(source, source_type, json.dumps(msg))
