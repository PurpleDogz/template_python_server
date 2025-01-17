import time

# import asyncio
# import asyncpool

"""
.. moduleauthor:: Barnaby Alderson <barnaby.alderson@iress.com>

This module contains classes to implement a simple thread pool
"""


class DurationTimer(object):
    def __init__(self):
        self.started = time.time()
        self.stopped = 0

    def start(self):
        self.started = time.time()
        self.stopped = 0
        return self

    def get_start(self):
        return self.started

    def get_stop(self):
        return self.stopped

    def stop(self):
        if self.started > 0:
            self.stopped = time.time()
        return self

    def duration(self):
        if self.stopped == 0:
            self.stopped = time.time()
        return int(round((self.stopped - self.started) * 1000, 0))

    def __str__(self):
        # if self.started == 0:
        #     return 'not-running'
        # if self.started > 0 and self.stopped == 0:
        #     return 'started: %d (running)' % self.started
        return DurationTimer.formatTime(self.duration())

    @staticmethod
    # convert to a readable string
    def formatTime(durationMS):
        if durationMS < 1000:
            return "%d millisecond(s)" % durationMS
        if durationMS < 60 * 1000:
            return "%d second(s)" % int(durationMS / 1000)
        min = int(durationMS / (60 * 1000))
        sec = int((durationMS / (60 * 1000) - min) * 60)
        if sec == 0:
            return "{MIN} minute(s)".format(MIN=min)
        return "{MIN} minute(s) {SEC} second(s)".format(MIN=min, SEC=sec)


"""
Usage:

Define class to run the function

class TaskRunnerCustom(taskrunner.TaskRunnerBase):

    @taskrunner.run_in_executor_loop
    def dorunWorkerTask(self, ctx, data):
        return ctx[0].myFunct(ctx[1], data)

Create a list of data objects and execute with parameters:

    lstRet = TaskRunnerCustom().run((api_helper, typeName), lstData, WORKER_THREAD_COUNT, "DataLoadPool", LOGGER)

Will block until complete

"""

# def run_in_executor_loop(f):
#     @functools.wraps(f)
#     def inner(*args, **kwargs):
#         loop = asyncio.get_running_loop()
#         return loop.run_in_executor(None, lambda: f(*args, **kwargs))
#     return inner

# class TaskRunnerBase(object):

#     def run(self, ctx, lstData, num_workers, name, logger, max_task_time=300, log_every_n=None):
#         logger.info('Creating Thread Pool [{}]: Threads={}, Tasks={}'.format(name, num_workers, len(lstData)))
#         ts = DurationTimer()
#         try:
#             loop = asyncio.get_event_loop()
#             ret = loop.run_until_complete(self.doRun(ctx, lstData, num_workers, name, logger, max_task_time, log_every_n))
#             tps = 0
#             if len(lstData) > 0 and ts.duration() > 0:
#                 tps = float(len(lstData)) / (float(ts.duration())/1000)
#             logger.info('Thread Pool Finished [{}]: Duration={}, TPS={:0.2f}'.format(name, str(ts), tps))
#             return ret
#         except KeyboardInterrupt:
#             print("Received exit, exiting")

#     async def doRun(self, ctx, lstData, num_workers, name, logger, max_task_time, log_every_n):

#         self.logger = logger

#         result_queue = asyncio.Queue()
#         async with asyncpool.AsyncPool(asyncio.get_event_loop(), num_workers=num_workers, name=name,
#                                        logger=logger,
#                                        worker_co=self.runWorkerTask, max_task_time=max_task_time,
#                                        log_every_n=log_every_n) as pool:
#             for item in lstData:
#                 await pool.push(result_queue, ctx, [item])
#         await result_queue.put(None)

#         results = []
#         for _ in range(result_queue.qsize()):
#             obj = result_queue.get_nowait()
#             if obj:
#                 results.extend(obj)
#         return results

#     @run_in_executor_loop
#     def dorunWorkerTask(self, ctx, data):
#         return None

#     async def runWorkerTask(self, result_queue, ctx, data):
#         self.logger.debug('RunTask: Data={}'.format(data))
#         await result_queue.put(await self.dorunWorkerTask(ctx, data))
