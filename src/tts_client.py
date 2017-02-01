# Standard library imports
import asyncio

# Package imports
from src import monitors
from src import common


class TTS(object):
    def __init__(self, loop, client_con):
        self.client_con = client_con
        self.loop = loop

        # Setup autospeak to send all speach requests to server automatically
        core = self._autospeak(monitors.speakQ)
        asyncio.ensure_future(core)

    async def _autospeak(self, queue):
        while True:
            request = dict(task="speak")
            request["text"] = await queue.get()
            self.client_con.send_data(request)
            queue.task_done()

    async def _wait_response(self, future, request):
        request["id"] = common.gen_random()
        queue = common.responseQ[request["id"]]
        self.client_con.send_data(request)
        ret = await queue.get()
        queue.task_done()
        del common.responseQ[request["id"]]
        future.set_result(ret["result"])

    def _future_response(self, request):
        future = asyncio.Future()
        asyncio.ensure_future(self._wait_response(future, request))
        self.loop.run_until_complete(future)
        return future.result()

    def get_rate(self):
        request = dict(task="get_voices")
        return self._future_response(request)









    @property
    def rate(self):
        """ Return the current speech rate """
        self._send_header("get_rate", "null")
        command, value = self._recv_header()
        if command == "property": return int(value)

    @rate.setter
    def rate(self, value):
        """
        Change the speach rate of the voice

        value : integer --- Rate to set the voice to

        Value must be between -10 to +10
        """
        value = int(value)
        if value < -10 or value > 10:
            raise ValueError("invalid rate %s" % value)
        else:
            self._send_header("set_rate", value)

    @property
    def volume(self):
        """ Return the current volume level """
        self._send_header("get_volume", "null")
        command, value = self._recv_header()
        if command == "property": return int(value)

    @volume.setter
    def volume(self, value):
        """
        Chagne the volume of the voice

        value : int --- level of the volume to change to
        """
        if value < 0 or value > 100:
            raise ValueError("invalid volume %s" % value)
        else:
            self._send_header("set_volume", value)

    def _get_voice_data(self):
        command, value = self._recv_header()
        if not command == "voicedata":
            print
            command, value
            return {}
        else:
            length = int(value)

        voicesData = []
        count = 0
        while count < length:
            left = length - count
            data = self.tcpsock.recv(CHUNK if left > CHUNK else left)
            count += len(data)
            voicesData.append(data)

        # Recombine voices into dict
        return [Voice(None, voiceID, name[0]) for voiceID, name in urlparse.parse_qs("".join(voicesData)).iteritems()]


    @property
    def voice(self):
        """ Return the current selected voice as a Voice object """
        self._send_header("get_voice", "null")
        return self._get_voice_data()[0]

    @voice.setter
    def voice(self, voice):
        """
        Change voice to selected voice Token

        value : Voice obj --- The voice of witch to change too
        """
        self._send_header("set_voice", len(voice.id))
        self.tcpsock.send(voice.id)

    def get_voices(self):
        """ Return list of avalable voices as a Voice object """
        self._send_header("get_voices", "null")
        return self._get_voice_data()















class Voice(object):
    """ Voice data object """

    def __init__(self, token, id, name, gender=None, languages=None):
        self.__id = id
        self.__name = name
        self.__gender = gender
        self.__languages = languages
        self._token = token

    @property
    def id(self):
        """ Return the id of the voice """
        return self.__id

    @property
    def id_basic(self):
        return self.__id.rsplit("\\", 1)[-1]

    @property
    def name(self):
        """ Return the name of the voice """
        return self.__name

    @property
    def gender(self):
        """ Return the gender of the voice """
        return self.__gender

    @property
    def languages(self):
        """ Return the languages of the voice """
        return self.__languages