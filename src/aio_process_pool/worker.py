import traceback
from multiprocessing import Pipe, Process

from .utils import SubprocessException, io_bound


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
        self._start_process()

    def _start_process(self):
        self.pipe, child_pipe = Pipe()
        self.process = Process(target=_worker_process, args=(child_pipe,))
        self.process.daemon = True
        self.process.start()
        self.is_working = False

    def _restart_process(self):
        self.shutdown()
        self._start_process()

    async def run(self, f, *args, **kwargs):
        assert f is not None
        assert not self.is_working

        self.is_working = True
        self.pipe.send((f, args, kwargs))

        # await pipe.recv
        try:
            res = await io_bound(self.pipe.recv)
        except EOFError:
            # called function is not available in child process -> restart & retry
            self._restart_process()
            return await self.run(f, *args, **kwargs)

        self.is_working = False

        return res

    def shutdown(self, kill=False):
        if not kill:
            try:
                self.pipe.send((None, None, None))
            except BrokenPipeError:
                pass
        else:
            self.process.kill()
        self.pipe.close()
        self.process.join()
