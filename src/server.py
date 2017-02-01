# Standard library imports
import asyncio

# Package imports
from src import common
from src import tts_server


class Server(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.peername = None
        self.handler = None

    def connection_made(self, transport):
        self.peername = transport.get_extra_info("peername")
        print("Connection from {}".format(self.peername))
        self.handler = common.ProtocolHandler(self)
        self.transport = transport

    def data_received(self, data):
        core = self.handler.stream_decode(data)
        asyncio.ensure_future(core)

    def send_data(self, data):
        stream = self.handler.stream_encode(data)
        self.transport.write(stream)

    def connection_lost(self, exc):
        print("Disconnected from {}".format(self.peername))
        self.transport = None
        self.peername = None


def run():
    # Fetch Event Loop
    loop = asyncio.get_event_loop()

    # Each client connection will create a new protocol instance
    coro = loop.create_server(Server, "127.0.0.1", 8888)
    server = loop.run_until_complete(coro)

    # Setup TTS command processor
    command_processor = tts_server.TTS()
    tts_task = asyncio.ensure_future(command_processor.start())

    # Serve requests until Ctrl+C is pressed
    try:
        print("Serving on {}".format(server.sockets[0].getsockname()))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.close()
        tts_task.cancel()
        loop.run_until_complete(server.wait_closed())
        loop.close()
