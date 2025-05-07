import asyncio
import concurrent
import concurrent.futures

from functools import partial

from .process_pool import ProcessPool

class Executor(ProcessPool, concurrent.futures.Executor):
    def __init__(self):
        self.futures_dict = {}
        super().__init__()

    def _set_running_or_notify_cancel(self) -> bool:
        if not super()._set_running_or_notify_cancel():
            return False

        task = asyncio.current_task()

        # if this task was not schedule by submit
        if not task in self.futures_dict:
            return True

        runable = self.futures_dict[task].set_running_or_notify_cancel()
        if not runable:
            del self.futures_dict[task]

        return runable

    def _task_done_callback(self, task):
        concurrent_future = self.futures_dict.pop(task)

        if (exception := task.exception()) is not None:
            concurrent_future.set_exception(exception)
        else:
            concurrent_future.set_result(task.result())

    def submit(self, fn, /, *args, **kwargs):
        task = asyncio.create_task(self.run(fn, *args, **kwargs))

        self.futures_dict[task] = concurrent.futures._base.Future()

        task.add_done_callback(self._task_done_callback)

        return self.futures_dict[task]

    def shutdown(self, wait=True, *, cancel_futures=False):
        if cancel_futures:
            for futures in self.futures_dict.values():
                futures.cancel()

        if not wait:
            raise ValueError("TODO: handle wait=False")

        super().shutdown(wait, cancel_futures=cancel_futures)

    async def map_async(self, fn, *iterables, timeout=None, chunksize=1):
        assert chunksize == 1
        assert timeout == None
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
