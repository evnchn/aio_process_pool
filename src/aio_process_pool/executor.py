import asyncio
import concurrent
import concurrent.futures

from functools import partial

from .process_pool import ProcessPool

class Executor(concurrent.futures.Executor):
    def __init__(self, max_workers=None):
        self._futures_dict = {}
        self._pool = ProcessPool(max_workers, self._set_running_or_notify_cancel)
        self.pending_shutdown = False

    def _set_running_or_notify_cancel(self, task) -> bool:
        assert task in self._futures_dict

        if self._futures_dict[task].set_running_or_notify_cancel():
            return True

        del self._futures_dict[task]
        return False

    def _task_done_callback(self, task):
        concurrent_future = self._futures_dict.pop(task)

        if (exception := task.exception()) is not None:
            concurrent_future.set_exception(exception)
        else:
            concurrent_future.set_result(task.result())

        if self.pending_shutdown and len(self._futures_dict) == 0:
            self._shutdown()

    def submit(self, fn, /, *args, **kwargs):
        # schedule execution as separate task
        task = asyncio.create_task(self._pool.run(fn, *args, **kwargs))

        # create future
        self._futures_dict[task] = concurrent.futures._base.Future()

        # add task.done callback
        task.add_done_callback(self._task_done_callback)

        # return future
        return self._futures_dict[task]

    async def map_async(self, fn, *iterables, timeout=None, chunksize=1):
        if not chunksize == 1:
            raise ValueError("chunksize != 1 is not implemented yet")
        if not timeout == None:
            raise ValueError("timeout != None is not implemented yet")

        loop = asyncio.get_event_loop()

        futures = [loop.run_in_executor(self, partial(fn, *args))
                   for args in zip(*iterables)]

        return await asyncio.gather(*futures)

    def map(self, fn, *iterables, timeout=None, chunksize=1):
        loop = asyncio.get_event_loop()

        if loop.is_running():
            raise RuntimeError("event loop already running, use map_async")

        coro = self.map_async(fn, *iterables, timeout=timeout, chunksize=chunksize)
        return loop.run_until_complete(coro)

    def _shutdown(self):
        self._pool.shutdown()

    def shutdown(self, wait=True, *, cancel_futures=False):
        if cancel_futures:
            for futures in self._futures_dict.values():
                futures.cancel()

        if not wait:
            self.pending_shutdown = True
            return

        self._shutdown()
