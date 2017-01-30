# Standard library imports
import asyncio

# Package imports
from src import common
from src import monitors


class AutoConnect(object):
    def __init__(self, loop, host, port):
        self.client = Client(self)
        self.connected = False
        self.con_fail = 0
        self.loop = loop
        self.host = host
        self.port = port

        # Set custom exception handler
        loop.set_exception_handler(self.excetpion_handler)

        # Attempting connection to server
        print("Attempting connection to {} on port {}".format(self.host, self.port))
        self.connect()

    def excetpion_handler(self, _, context):
        # Fetch exception if available
        exc = context.get("exception")

        # Only reconnect if exception is an OSError of Errno 111
        if self.connected is False and self.con_fail <= 3 and isinstance(exc, OSError) and "Errno 111" in exc.args[0]:
            print("Unable to connect")
            self.reconnect()
        else:
            self.loop.stop()
            raise exc

    def reconnect(self, delay=5):
        self.loop.call_later(delay, self.connect)
        self.con_fail += 1

    def connect(self):
        coro = self.loop.create_connection(self, host=self.host, port=self.port)
        asyncio.ensure_future(coro)

    def __call__(self):
        return self.client


class Client(asyncio.Protocol):
    def __init__(self, manager):
        self.transport = None
        self.manager = manager

        # Setup handler to process socket data
        self.handler = common.ProtocolHandler(self)

    def connection_made(self, transport):
        print("Connection made to server")
        self.manager.connected = True
        self.manager.failed_con = 0
        self.transport = transport

    def data_received(self, data):
        core = self.handler.stream_decode(data)
        asyncio.ensure_future(core)

    def connection_lost(self, exc):
        print("The server closed the connection")
        print("Attempting reconnect")
        self.manager.connected = False
        self.manager.reconnect()


def run():
    # Fetch Event Loop
    loop = asyncio.get_event_loop()

    # Setup Automatic connection manager
    AutoConnect(loop, "localhost", 8888)

    # Setup clipboard monitor
    clipboard_moniter = monitors.clipboard()
    clib_task = asyncio.ensure_future(clipboard_moniter)

    # Make requests until Ctrl+C is pressed
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        clib_task.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()
