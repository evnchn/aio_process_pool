import traceback
from multiprocessing import Pipe, Process

from .utils import SubprocessException, io_bound


def _worker_process(child_pipe):
    try:
        while True:
            func, args, kwargs = child_pipe.recv()
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


class Worker:
    def __init__(self):
        self.pipe, child_pipe = Pipe()
        self.process = Process(target=_worker_process, args=(child_pipe,))
        self.process.daemon = True
        self.process.start()

    async def run(self, f, *args, **kwargs):
        assert f is not None

        self.pipe.send((f, args, kwargs))
        return await io_bound(self.pipe.recv)

    def shutdown(self, kill=False):
        if not kill:
            self.pipe.send((None, None, None))
        else:
            self.process.kill()
        self.process.join()
