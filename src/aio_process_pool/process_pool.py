import asyncio
import os

from .worker import Worker as Worker


class ProcessPool:
    def __init__(self, max_workers=None, set_running_callback=None):
        if max_workers is None:
            max_workers = min(os.cpu_count() or 1, 61)
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")

        self.worker = [Worker() for _ in range(max_workers)]
        self.pool = asyncio.Queue()
        for w in self.worker:
            self.pool.put_nowait(w)

        self.cancel_futures = False
        self.set_running_callback = set_running_callback or (lambda _: True)

    async def run(self, f, *args, **kwargs):
        worker = await self.pool.get()
        assert worker.process.is_alive()

        task = asyncio.current_task()
        result, exception = None, None
        if self.set_running_callback(task):
            result, exception = await worker.run(f, *args, **kwargs)

        self.pool.put_nowait(worker)

        if exception is not None:
            raise exception
        return result

    async def map(self, fn, *iterables):
        futures = [self.run(fn, *args) for args in zip(*iterables)]
        return await asyncio.gather(*futures)

    def is_shutdown(self):
        return len(self.worker) == self.pool.qsize() == 0

    def shutdown(self, kill=False):
        # assert all workers are idle
        assert len(self.worker) == self.pool.qsize()

        for w in self.worker:
            w.shutdown(kill=kill)

        self.worker.clear()
        while not self.pool.empty():
            self.pool.get_nowait()
        # TODO in future >= 3.13: use self.pool.shutdown
