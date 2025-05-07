import asyncio
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
        self.futures = set()
        for w in self.worker:
            self.pool.put_nowait(w)

    async def _get_worker(self):
        assert len(self.worker) > 0

        if self.pool.empty():
            return await self.pool.get()

        return self.pool.get_nowait()

    async def run(self, f, *args, **kwargs):
        worker = await self._get_worker()
        assert worker.process.is_alive()

        result, exception = await worker.run(f, *args, **kwargs)

        self.pool.put_nowait(worker)

        if exception is not None:
            raise exception

        return result

    def submit(self, fn, /, *args, **kwargs):
        task = asyncio.create_task(self.run(fn, *args, **kwargs))

        self.futures.add(task)
        task.add_done_callback(self.futures.discard)

        return task

    def shutdown(self, wait=True, *, cancel_futures=False):
        if cancel_futures:
            for f in self.futures:
                f.cancel()

        if not wait:
            raise ValueError("TODO: handle wait=False")

        for w in self.worker:
            w.shutdown(kill=False)

        self.worker.clear()
        # self.pool.shutdown() #this is available >= 3.13
        self.pool = asyncio.Queue() # reset / clear pool
