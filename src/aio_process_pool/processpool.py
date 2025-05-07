import asyncio
import concurrent
import os

from .worker import Worker as _Worker


class AsyncProcessPool:
    def __init__(self, max_size=os.cpu_count()):
        if max_size is None:
            max_size = 1
        if max_size < 1:
                 raise ValueError("max_size must be at least 1")

        self.worker = [_Worker() for _ in range(max_size)]
        self.pool = asyncio.Queue()
        self.futures_dict = {}
        for w in self.worker:
            self.pool.put_nowait(w)

    async def _get_worker(self):
        assert len(self.worker) > 0

        if self.pool.empty():
            return await self.pool.get()

        return self.pool.get_nowait()

    async def run(self, f, *args, **kwargs):
        # get worker
        worker = await self._get_worker()
        assert worker.process.is_alive()

        # check if future was cancelled if a corresponding future exists
        task = asyncio.current_task()
        cancelled = False
        if task in self.futures_dict:
            cancelled = not self.futures_dict[task].set_running_or_notify_cancel()

        # execute
        if not cancelled:
            result, exception = await worker.run(f, *args, **kwargs)
        else:
            result, exception = None, None
            del self.futures_dict[task]

        # return worker
        self.pool.put_nowait(worker)

        # raise exception if necessary or return result
        if exception is not None:
            raise exception

        return result

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
            for cfuture in self.futures_dict.values():
                cfuture.cancel()

        if not wait:
            raise ValueError("TODO: handle wait=False")

        for w in self.worker:
            w.shutdown(kill=False)

        self.worker.clear()
        # self.pool.shutdown() #this is available >= 3.13
        self.pool = asyncio.Queue() # reset / clear pool
