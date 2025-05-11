import asyncio
import traceback
from multiprocessing import Pipe, Process

from .utils import EventInterrupter, SubprocessException, io_bound


def _worker_process(child_pipe):
    try:
        while True:
            try:
                func, args, kwargs = child_pipe.recv()
            except AttributeError:
                # the requested func is not available in this process
                # -> restart
                break

            if func is None:
                break

            result, exception = None, None
            try:
                result = func(*args, *kwargs)
            except Exception as e:
                exception = SubprocessException(type(e).__name__,
                                                str(e),
                                                traceback.format_exc())

            child_pipe.send((result, exception))
    except KeyboardInterrupt:
        pass
    finally:
        child_pipe.close()


class Worker:
    def __init__(self):
        self._shutdown_event = asyncio.Event()
        self._lock = asyncio.Lock()
        self._start_process()

    def _start_process(self):
        self.pipe, child_pipe = Pipe()
        self.process = Process(target=_worker_process, args=(child_pipe,))
        self.process.daemon = True
        self.process.start()

    def _restart_process(self):
        self._shutdown(restart=True)
        self._start_process()

    async def _run(self, f, *args, **kwargs):
        assert f is not None
        assert not self._shutdown_event.is_set()

        self.pipe.send((f, args, kwargs))

        try:
            return await io_bound(self.pipe.recv)
        except EOFError:
            if self._shutdown_event.is_set():
                # shutdown killed the child process
                raise asyncio.CancelledError()

            # called function is not available in child process -> restart & retry
            self._restart_process()
            return await self._run(f, *args, **kwargs)

    async def run(self, f, *args, **kwargs):
        if self._shutdown_event.is_set():
            raise asyncio.CancelledError()

        async with EventInterrupter(self._shutdown_event):
            await self._lock.acquire()

        try:
            return await self._run(f, *args, **kwargs)
        finally:
            self._lock.release()

    def _shutdown(self, kill=False, restart=False):
        if not restart:
            self._shutdown_event.set()

        if not kill:
            try:
                self.pipe.send((None, None, None))
            except BrokenPipeError:
                # this happens if the child process restarts, see _run
                pass
        else:
            self.process.kill()

        self.process.join()
        self.pipe.close()

    def shutdown(self, kill=False):
        self._shutdown(kill, restart=False)
