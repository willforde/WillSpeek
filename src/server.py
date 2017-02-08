# Standard library imports
import asyncio

# Package imports
from src import common
from src import tts_server


class ServerTCP(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.peername = None
        self.handler = None
        self.buffer = []

    def connection_made(self, transport):
        self.peername = transport.get_extra_info("peername")
        print("Connection from {}".format(self.peername))
        self.handler = common.ProtocolHandler(self)
        self.transport = transport

        # Transmit any delayed buffered data
        # while the connection was lost
        while self.buffer:
            data = self.buffer.pop(0)
            self.send_data(data)

    def data_received(self, data):
        core = self.handler.stream_decode(data)
        asyncio.ensure_future(core)

    def send_data(self, data):
        if self.transport:
            stream = self.handler.stream_encode(data)
            self.transport.write(stream)
        else:
            self.buffer.append(data)

    def connection_lost(self, exc):
        print("Disconnected from {}".format(self.peername))
        self.transport = None
        self.peername = None


class ServerUDP:
    def __init__(self):
        self.transport = None
        self.buffer = []

    def connection_made(self, transport):
        self.transport = transport

        # Transmit any delayed buffered data
        # while the connection was lost
        while self.buffer:
            data = self.buffer.pop(0)
            self.send_audio(data)

    def datagram_received(self, data, addr):
        pass

    def send_audio(self, audio_fragment):
        if self.transport:
            self.transport.sendto(audio_fragment)
        else:
            self.buffer.append(audio_fragment)

    def connection_lost(self, exc):
        print(exc)


def run(host, port):
    # Fetch Event Loop
    loop = asyncio.get_event_loop()

    # One protocol instance will be created to serve all client TCP requests
    coro = loop.create_server(ServerTCP, host, port)
    server_tcp = loop.run_until_complete(coro)

    # One protocol instance will be created to serve all client UDP requests
    coro = loop.create_datagram_endpoint(ServerUDP, local_addr=(host, port))
    server_udp, protocol = loop.run_until_complete(coro)

    # Setup TTS command processor
    command_processor = tts_server.TTS(server_udp)
    coro = command_processor.start()
    tts_task = asyncio.ensure_future(coro)

    # Serve requests until Ctrl+C is pressed
    try:
        print("Serving on {}".format(server_tcp.sockets[0].getsockname()))
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server_tcp.close()
        server_udp.close()
        tts_task.cancel()
        loop.run_until_complete(server_tcp.wait_closed())
        loop.close()
