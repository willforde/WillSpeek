# Standard library imports
import asyncio

# Package imports
from src import common
from src import monitors
from src import playback
from src import tts_client


class AutoConnect(object):
    def __init__(self, loop, host, port):
        self.client = ClientTCP(loop, self)
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
        if self.connected is False and isinstance(exc, OSError) and "Errno 111" in exc.args[0]:
            if self.con_fail <= 3:
                print("Unable to connect")
                self.reconnect()
            else:
                print("Aborting reconnection")
                self.loop.stop()
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


class ClientTCP(asyncio.Protocol):
    def __init__(self, loop, manager):
        self.udp_addr = None
        self.transport = None
        self.manager = manager
        self.loop = loop
        self.buffer = []
        self.tts = None

        # Setup handler to process socket data
        self.handler = common.ProtocolHandler(self)

    def connection_made(self, transport):
        print("Connection made to server")
        self.manager.connected = True
        self.manager.failed_con = 0
        self.transport = transport

        # Initialize Speach engine with saved settings
        init_core = self.initialize()
        asyncio.ensure_future(init_core)

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
        print("The server closed the connection")
        print("Attempting reconnect")
        self.manager.connected = False
        self.manager.reconnect()
        self.transport = None

        # Cancel all Futures if connection is lost
        for future in common.responseF.values():
            future.cancel()

    async def initialize(self):
        # Create a UDP client if not already created
        if self.tts is None:
            connect = self.loop.create_datagram_endpoint(ClientUDP, remote_addr=(self.manager.host, self.manager.port))
            transport, _ = await asyncio.ensure_future(connect)
            udp_addr = transport.get_extra_info("peername")

            # Setup TTS
            self.tts = tts_client.TTS(self.loop, self.send_data, udp_addr)

        # Fetch configuration
        config = common.load_config("settings.json")

        # Set required voice
        voices = await self.tts.get_voices()
        for voice in voices:
            if voice.name == config["voice"]:
                await self.tts.set_voice(voice)

        # Set voice rate
        await self.tts.set_rate(config["rate"])

        # Set volume level
        await self.tts.set_volume(config["volume"])

        # Transmit any delayed buffered data
        # while the connection was lost
        while self.buffer:
            data = self.buffer.pop(0)
            self.send_data(data)


class ClientUDP:
    def __init__(self):
        self.transport = None

    def connection_made(self, transport):
        self.transport = transport

        # Setup keep alive requests
        core = self.keep_alive()
        asyncio.ensure_future(core)

    async def keep_alive(self):
        # Send an empty string to UDP server every minute
        # to keep firewall mapping alive if needed
        while True:
            self.transport.sendto(b"")
            await asyncio.sleep(60)

    def datagram_received(self, data, addr):
        # Send audio frames to playback thread
        # playback.frames.put(data)
        pass

    def connection_lost(self, exc):
        print("UDP Connection Lost {}".format(exc))


def run(host, port):
    # Fetch Event Loop
    loop = asyncio.get_event_loop()

    # Setup Automatic connection manager
    AutoConnect(loop, host, port)

    # Setup clipboard monitor
    clipboard_moniter = monitors.clipboard()
    clib_task = asyncio.ensure_future(clipboard_moniter)

    # Setup audio playback
    player, stream = playback.listen()

    # Make requests until Ctrl+C is pressed
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stream.close()
        player.terminate()
        clib_task.cancel()
        loop.run_until_complete(loop.shutdown_asyncgens())
        loop.stop()
        loop.close()
