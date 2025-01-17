import threading

DEF_SLEEP_INTERVAL = 10

###################################################
# Service


class BaseService(threading.Thread):
    def __init__(
        self,
        name="Default",
        interval=DEF_SLEEP_INTERVAL,
        logger=None,
        daemon=False,
    ):
        self.logger = logger
        super().__init__(daemon=daemon)
        self._kill = threading.Event()
        self.name = name
        self._interval = interval

    def kill(self):
        self._kill.set()

    def run(self):
        self.logger.info(
            "Start Service [Name = {}, Timer = {}sec]".format(self.name, self._interval)
        )
        while True:
            self.__check()
            is_killed = self._kill.wait(self._interval)
            if is_killed:
                break
        self.logger.info("Stop Service [Name = {}]".format(self.name))

    def __check(self):
        try:
            self.check()
        except Exception as ex:
            self.logger.exception(
                "{} : Timer Event Failed -> {}".format(self.name, str(ex)), exc_info=ex
            )
            pass

    def check(self):
        pass
