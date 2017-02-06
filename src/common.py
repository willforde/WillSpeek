# Standard library imports
from base64 import b64encode, b64decode
from random import random
import collections
import asyncio
import json
import os

# Create Queue for all command
requestQ = asyncio.Queue()
responseF = collections.defaultdict(asyncio.Future)

# Create path to config folder
CWDPATH = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))
CONFIGPATH = os.path.join(CWDPATH, "data")


def gen_random():
    # Generate a unique id
    while True:
        val = str(int(random() * 1000000000))
        if val not in responseF:
            return val


def load_config(filename):
    filepath = os.path.join(CONFIGPATH, filename)
    with open(filepath, "rb") as opened_file:
        return json.load(opened_file)


class ProtocolHandler(object):
    def __init__(self, client):
        self._client = client
        self._buffer = []

    async def stream_decode(self, data):
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
        for request in filter(None, requests):
            # Decode the request
            json_data = b64decode(request)
            json_obj = json.loads(json_data, encoding="utf8", object_hook=self.dict_to_voice)

            # Decode the data element if available into a "utf8" encoded string
            if "params" in json_obj and "text" in json_obj["params"]:
                raw_data = b64decode(json_obj["params"]["text"].encode("ascii"))
                json_obj["params"]["text"] = raw_data.decode("utf8")

            # Append to command to the list of commands
            json_obj["_client"] = self._client

            # Add response to Queue, response, request
            requestid = json_obj.get("id", "0")
            if requestid in responseF:
                future = responseF[requestid]
                future.set_result(json_obj["response"])
            else:
                await requestQ.put(json_obj)

    @staticmethod
    def stream_encode(data):
        """
        Convert a dictionary into a base64 encoded data, ready for network transfer.

        :param dict data: Dictionary to convert
        :return: Base64 encoded data
        :rtype: bytes
        """

        # Remove client stream object if exists
        if "_client" in data:
            del data["_client"]

        # Convert raw_data to base64 if exists
        if "params" in data and "text" in data["params"]:
            data["params"]["text"] = b64encode(data["params"]["text"].encode("utf8")).decode("ascii")

        # Convert dict into a serialized string ready for network transfer
        stream = json.dumps(data, default=ProtocolHandler.voice_to_dict).encode("utf8")
        return b64encode(stream) + b"|"

    @staticmethod
    def voice_to_dict(obj):
        # Check for a Voice object
        if isinstance(obj, Voice):
            # Convert voice object into a dict
            data = {"__class__": "Voice"}
            data.update(obj.__dict__)
            return data

        # Return unmodified object
        return obj

    @staticmethod
    def dict_to_voice(dct):
        # Convert any serialized voice object back into a voice object
        if "__class__" in dct and dct["__class__"] == "Voice":
            del dct["__class__"]
            return Voice(**dct)

        # Return unmodified object
        return dct


# Setup Voice object
class Voice(object):
    def __init__(self, voiceid, name, gender):
        self.voiceid = voiceid
        self.gender = gender
        self.name = name
