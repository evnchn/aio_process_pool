import asyncio
import os

from .worker import Worker as Worker


class ProcessPool:
    def __init__(self, max_workers=None, set_running_callback=None):
        if max_workers is None:
            max_workers = min(os.cpu_count() or 1, 61)
            # TODO in future: os.cpu_count() -> os.process_cpu_count()
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

    def shutdown(self, kill=False):
        for w in self.worker:
            w.shutdown(kill=kill)

        self.worker.clear()
        self.pool = asyncio.Queue() # reset / clear pool
        # TODO in future: checkout self.pool.shutdown() available >= 3.13
