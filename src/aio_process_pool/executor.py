import asyncio
import concurrent
import concurrent.futures
from threading import Condition

from functools import partial

from .process_pool import ProcessPool

class Executor(concurrent.futures.Executor):
    def __init__(self, max_workers=None):
        self._futures_dict = {}
        self._pool = ProcessPool(max_workers, self._set_running_or_notify_cancel)

        self._is_shutdown_pending = False
        self._shutdown_done_event = asyncio.Event()
        self._shutdown_done = Condition()

    def _set_running_or_notify_cancel(self, task) -> bool:
        return self._futures_dict[task].set_running_or_notify_cancel()

    def _task_done_callback(self, task):
        assert task in self._futures_dict
        future = self._futures_dict.pop(task)

        if not future.cancelled():
            if (exception := task.exception()) is not None:
                future.set_exception(exception)
            else:
                future.set_result(task.result())

        if self._is_shutdown_pending and len(self._futures_dict) == 0:
            self._shutdown()

            self._shutdown_done.acquire()
            self._shutdown_done.notify_all()
            self._shutdown_done.release()

            self._shutdown_done_event.set()

    def submit(self, fn, /, *args, **kwargs):
        if self._is_shutdown_pending:
            raise RuntimeError("shutdown pending: can't schedule new work")

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

    def _prepare_shutdown(self, cancel_futures):
        self._is_shutdown_pending = True
        if cancel_futures:
            for future in self._futures_dict.values():
                future.cancel()

    def _shutdown(self):
        self._pool.shutdown()

    async def _pending_async_shutdown(self):
        while len(self._futures_dict) > 0:
            await self._shutdown_done_event.wait()
            self._shutdown_done_event.clear()
        self._shutdown()

    async def shutdown_async(self, wait=True, *, cancel_futures=False):
        self._prepare_shutdown(cancel_futures)

        coro = self._pending_async_shutdown()
        if wait:
            await coro
        else:
            asyncio.create_task(coro)

    def shutdown(self, wait=True, *, cancel_futures=False):
        self._prepare_shutdown(cancel_futures)

        if len(self._futures_dict) == 0:
            self._shutdown()
            return

        if wait:
            self._shutdown_done.acquire()
            self._shutdown_done.wait_for(lambda: len(self._futures_dict) == 0)
            self._shutdown_done.release()

    def is_shutdown(self):
        return self._pool.is_shutdown()

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.shutdown_async()
        return False
