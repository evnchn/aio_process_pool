"""the content of this file is borrowed from nicegui.run"""

import asyncio
from functools import partial


class SubprocessException(Exception):
    """A picklable exception to represent exceptions raised in subprocesses."""

    def __init__(self, original_type, original_message, original_traceback):
        self.original_type = original_type
        self.original_message = original_message
        self.original_traceback = original_traceback
        super().__init__(f'{original_type}: {original_message}')

    def __reduce__(self):
        return (SubprocessException, (self.original_type,
                                      self.original_message,
                                      self.original_traceback))

    def __str__(self):
        return (f'Exception in subprocess:\n'
                f'  Type: {self.original_type}\n'
                f'  Message: {self.original_message}\n'
                f'  {self.original_traceback}')


async def io_bound(callback, *args, **kwargs):
    """Run an I/O-bound function in a separate thread."""
    loop = asyncio.get_event_loop()
    # first parameter None -> run in default ThreadPoolExecutor
    return await loop.run_in_executor(None, partial(callback, *args, **kwargs))


class EventInterrupter:
    def __init__(self, e):
        self.event = e
        self.task = asyncio.current_task()
        self.cancel_task = None

    async def __aenter__(self):
        loop = asyncio.get_running_loop()
        self.cancel_task = loop.create_task(self.cancel_on_trigger())
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        assert self.cancel_task
        if not self.cancel_task.done():
            self.cancel_task.cancel()
        return None

    async def cancel_on_trigger(self):
        await self.event.wait()
        assert self.task
        self.task.cancel()
