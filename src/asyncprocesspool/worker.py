import traceback
from multiprocessing import Pipe, Process

from .utils import SubprocessException, io_bound as _io_bound


def _worker_process(tx):
    try:
        while True:
            func, args, kwargs = tx.recv()
            if func is None:
                break

            result, exception = None, None
            try:
                result = func(*args, *kwargs)
            except Exception as e:
                exception = SubprocessException(type(e).__name__,
                                                str(e),
                                                traceback.format_exc())

            tx.send((result, exception))
    except KeyboardInterrupt:
        pass


class Worker:
    def __init__(self):
        self.rx, tx = Pipe()
        self.process = Process(target=_worker_process, args=(tx,))
        self.process.daemon = True
        self.process.start()

    async def run(self, f, *args, **kwargs):
        assert f is not None

        self.rx.send((f, args, kwargs))
        return await _io_bound(self.rx.recv)

    def shutdown(self, kill=False):
        if not kill:
            self.rx.send((None, None, None))
        else:
            self.process.kill()
        self.process.join()
