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
        # Wait for a command to come in
        command = await commandQ.get()
        method = getattr(self, command.pop("task"))
        client_connection = command.pop("client")

        try:
            result = method(**command)
        except Exception as e:
            result = dict(success=False, msg=str(e))

        # If no result was returned then set success to false
        if result is None:
            result = dict(success=False, msg="missing response")

        # Return a response if the client is expecting one
        if "id" in command:
            response = dict(id=command["id"], response=result)
            client_connection.send_data(response)

        # Mark task as done
        command.task_done()


class TTS(Dispatcher):
    def speek(self, text=""):
        """ Send text to tts engine and speak """
        self._engine.Speak(text)
        return StringIO(bytearray(self._stream.GetData()))

    def stop(self):
        self._engine.Speak("", 3)
        return dict(success=True)

    def get_rate(self):
        """ Return the current speech rate """
        rate = self._engine.Rate
        return dict(success=True, rate=rate)

    def set_rate(self, rate):
        """
        Change the speach rate of the voice

        :param rate: Rate to set the voice to
        :type rate: integer

        Rate must be between -10 and +10
        """
        if rate < -10 or rate > 10:
            raise ValueError("invalid rate {}".format(rate))
        else:
            self._engine.Rate = rate
            return dict(success=True)

    def get_volume(self):
        """ Return the current volume level """
        volume = self._engine.Volume
        return dict(success=True, volume=volume)

    def set_volume(self, volume):
        """
        Chagne the volume of the voice

        value : int --- level of the volume to change to
        """
        if volume < 0 or volume > 100:
            raise ValueError("invalid volume {}".format(volume))
        else:
            self._engine.Volume = volume
            return dict(success=True)

    def get_voices(self):
        """ Return list of avalable voices as a Voice object """
        voices = []
        for voice in self._engine.GetVoices():
            voiceid = voice.Id
            name = voice.GetDescription()
            gender = voice.GetAttribute("Gender")
            voices.append(dict(voiceid=voiceid, name=name, gender=gender))

        # Return a list of all available voices
        return dict(success=True, voices=voices)

    def get_voice(self):
        """ Return the current selected voice as a Voice object """
        _voice = self._engine.Voice
        voice = dict(voiceid=_voice.Id, name=_voice.GetDescription(), gender=_voice.GetAttribute("Gender"))
        return dict(success=True, voice=voice)

    def set_voice(self, voiceid):
        # Search all voices for given voiceid
        for voice in self._engine.GetVoices():
            if voice.Id == voiceid:
                self._engine.Voice = voice
                return dict(success=True)


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
