# Standard Library Imports
from io import StringIO
import asyncio

# Package Imports
from src import common

# Dependency Packages
from comtypes.client import CreateObject

# Fetch the Queue commands
commandQ = common.requestQ


class Dispatcher(object):
    def __init__(self):
        # Setup TTS Engine
        self._engine = None
        self._stream = None
        self.initialize_engine()

    def initialize_engine(self):
        self._engine = CreateObject("SAPI.SPVoice")
        self._stream = CreateObject("SAPI.SpMemoryStream")
        self._engine.AudioOutputStream = self._stream

    async def start(self):
        command = await commandQ.get()
        method = getattr(self, command.pop("task"))
        client_connection = command.pop("client")

        try:
            result = method(**command)
        except Exception:
            print(Exception)
        else:
            client_connection.transport.write(result)

        command.task_done()


class TTS(Dispatcher):
    def speek(self, text=""):
        """ Send text to tts engine and speak """
        self._engine.Speak(text)
        return StringIO(bytearray(self._stream.GetData()))

    def stop(self):
        self._engine.Speak("", 3)
        return "ok"

    def get_voices(self):
        """ Return list of avalable voices as a Voice object """
        return [Voice(attr, attr.Id, attr.GetDescription()) for attr in self._engine.GetVoices()]

    def get_voice(self):
        """ Return the current selected voice as a Voice object """
        _voice = self._engine.Voice
        return Voice(_voice, _voice.Id, _voice.GetDescription())

    def set_voice(self, value):
        """
        Change voice to selected voice Token

        value : Voice obj --- The voice of witch to change too
        """
        self._engine.Voice = value._token

    def get_rate(self):
        """ Return the current speech rate """
        return self._engine.Rate

    def set_rate(self, value):
        """
        Change the speach rate of the voice

        value : integer --- Rate to set the voice to

        Value must be between -10 to +10
        """
        if value < -10 or value > 10:
            raise ValueError("invalid rate %s" % value)
        else:
            self._engine.Rate = value

    def get_volume(self):
        """ Return the current volume level """
        return self._engine.Volume

    def set_volume(self, value):
        """
        Chagne the volume of the voice

        value : int --- level of the volume to change to
        """
        if value < 0 or value > 100:
            raise ValueError("invalid volume %s" % value)
        else:
            self._engine.Volume = value


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
