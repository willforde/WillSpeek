from base64 import b64encode, b64decode
from argparse import ArgumentParser
from tkinter import Tk, TclError
import asyncio
import json


# Fetch Event Loop
loop = asyncio.get_event_loop()

# Create Parser to parse the required arguments
parser = ArgumentParser(description="Text to speech client/server")

# Add argument for client mode
parser.add_argument("-s", "--server", action="store_true", default=False, help="Switch to Server Mode")
args = parser.parse_args()


class ClipboardMonitor(object):
    """ Class to monitor clipboard chnages """

    def __init__(self, queue):
        # Setup clipboard access
        self.gui = Tk()
        self.gui.withdraw()
        self.queue = queue

    async def start(self):
        prev_text = None
        while True:
            # Check the clipboard for data
            clipboard_text = await self.get_clipboard_text()
            if prev_text is None:
                prev_text = clipboard_text

            elif clipboard_text and not clipboard_text == prev_text:
                prev_text = clipboard_text
                await self.queue.put(clipboard_text)

            # Sleep for 50ms in order to loop 20 times a second
            await asyncio.sleep(.05)

    async def get_clipboard_text(self):
        try:
            return self.gui.clipboard_get()
        except TclError:
            await asyncio.sleep(1)
            return False


class DataProtocol(object):
    def __init__(self):
        self._buffer = []

    def stream_to_dict(self, data):
        """
        Convert a data stream from a TCP socket into a dictionary.

        :param data: Raw data from socket
        :type data: bytes
        """
        # Add data to buffer for later reassembly
        self._buffer.append(data)

        # If we don't have a closing bracket then
        # we must not have all the data yet
        if b"|" not in data:
            return None

        # We have delimiter so reassemble all buffered data
        full_stream = b"".join(self._buffer)
        requests = full_stream.split(b"|")
        self._buffer = []

        # Remove the last request item and if it's not empty then we must have an incomplete request
        # The incomplete request will be added to a new buffer for later reassembly
        last_request = requests.pop()
        if last_request:
            self._buffer.append(last_request)

        # Rebuild the data structure from a `base64` encoded string into a `dict`
        commands = []
        for request in filter(None, requests):
            # Decode the request
            json_data = b64decode(request)
            json_obj = json.loads(json_data, encoding="ascii")

            # Decode the data element if available into a "utf8" encoded string
            if "raw_string" in json_obj:
                raw_data = b64decode(json_obj["raw_string"].encode("ascii"))
                json_obj["raw_string"] = raw_data.decode("utf8")

            # Append to command to the list of commands
            commands.append(json_obj)

        return commands

    def dict_to_stream(self, data):
        """
        Convert a dictionary into a base64 encoded data, ready for network transfer.

        :param dict data: Dictionary to convert
        :return: Base64 encoded data
        :rtype: bytes
        """

        # Convert raw_data to base64 if exists
        if "raw_string" in data:
            data["raw_string"] = b64encode(data["raw_string"].encode("utf8")).decode("ascii")

        # Convert dict into a serialized string ready for network transfer
        stream = json.dumps(data).encode("ascii")
        return b64encode(stream) + b"|"


class Client(asyncio.Protocol):
    def __init__(self, speachqueue, host, port):
        self.failed_connections = 0
        self.connected = False
        self.transport = None
        self.host = host
        self.port = port

        self.queue = speachqueue
        self.data_handler = DataProtocol()

        # Attemp to connection to server
        print("Attempting to connect to {} on port {}".format(self.host, self.port))
        self.connect()

        #
        core = self.communicate()
        asyncio.ensure_future(core)

    async def communicate(self):
        while True:
            text = await self.queue.get()
            data = {"command": "speak", "raw_string": text}
            self.send_data(data)
            self.queue.task_done()

    def connection_made(self, transport):
        print("Connected to Server")
        self.transport = transport
        self.connected = True

        data = {"client": "hello server", "work": "true"}
        self.send_data(data)

    def data_received(self, data):
        data = self.data_handler.stream_to_dict(data)
        print("received {}".format(data))

    def send_data(self, data):
        stream = self.data_handler.dict_to_stream(data)
        self.transport.write(stream)

    def connection_lost(self, exc):
        print("The server closed the connection")
        print("Attempting reconnection")
        self.connected = False
        self.reconnect(5)

    def __call__(self):
        return self

    def excetpion_handler(self, loop, context):
        exception = context["exception"]
        self.failed_connections += 1

        if self.connected is False and self.failed_connections <= 25 and \
                isinstance(exception, OSError) and "[Errno 111]" in exception.args[0]:
            print("Unable to connect.")
            self.reconnect(5)
        else:
            loop.stop()
            raise exception

    def reconnect(self, delay):
        # Sleep for given delay and then reconnect
        loop.call_later(delay, self.connect)

    def connect(self):
        loop.set_exception_handler(self.excetpion_handler)
        coro = loop.create_connection(self, host=self.host, port=self.port)
        asyncio.ensure_future(coro)


class Server(asyncio.Protocol):
    def __init__(self):
        self.transport = None
        self.data_handler = DataProtocol()

    def connection_made(self, transport):
        peername = transport.get_extra_info('peername')
        print('Connection from {}'.format(peername))
        self.transport = transport

    def data_received(self, data):
        data = self.data_handler.stream_to_dict(data)
        print("received {}".format(data))

        data = {"server": "hello client", "work": "true"}
        self.send_data(data)

    def send_data(self, data):
        stream = self.data_handler.dict_to_stream(data)
        self.transport.write(stream)


def client_mode():
    speachqueue = asyncio.Queue()

    Client(speachqueue, "localhost", 8888)
    moniter = ClipboardMonitor(speachqueue)
    core = moniter.start()
    asyncio.ensure_future(core)

    try:
        loop.run_forever()
    except KeyboardInterrupt:
        loop.stop()

    loop.close()


def server_mode():
    # Each client connection will create a new protocol instance
    coro = loop.create_server(Server, '127.0.0.1', 8888)
    server = loop.run_until_complete(coro)

    # Serve requests until Ctrl+C is pressed
    print("Serving on {}".format(server.sockets[0].getsockname()))
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        pass
    finally:
        # Close the server
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()


if __name__ == '__main__':
    if args.server is True:
        server_mode()
    else:
        client_mode()
