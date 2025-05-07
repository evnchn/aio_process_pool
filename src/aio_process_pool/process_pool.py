import asyncio
import os

from .worker import Worker as _Worker


class ProcessPool:
    def __init__(self, max_workers=None):
        if max_workers is None:
            max_workers = min(os.cpu_count() or 1, 61)
            # TODO in future: os.cpu_count() -> os.process_cpu_count()
        if max_workers < 1:
            raise ValueError("max_workers must be at least 1")

        self.worker = [_Worker() for _ in range(max_workers)]
        self.pool = asyncio.Queue()
        for w in self.worker:
            self.pool.put_nowait(w)

        self.cancel_futures = False

    def _set_running_or_notify_cancel(self) -> bool:
        if self.cancel_futures:
            raise asyncio.CancelledError
        return True

    async def run(self, f, *args, **kwargs):
        worker = await self.pool.get()
        assert worker.process.is_alive()

        result, exception = None, None
        if self._set_running_or_notify_cancel():
            result, exception = await worker.run(f, *args, **kwargs)

        self.pool.put_nowait(worker)

        if exception is not None:
            raise exception
        return result

    def shutdown(self, wait=True, *, cancel_futures=False):
        if cancel_futures:
            self.cancel_futures = cancel_futures

        for w in self.worker:
            w.shutdown(wait=wait)

        self.worker.clear()
        self.pool = asyncio.Queue() # reset / clear pool
        # TODO in future: checkout self.pool.shutdown() available >= 3.13
