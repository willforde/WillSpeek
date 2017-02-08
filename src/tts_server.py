# Standard Library Imports
from io import StringIO

# Package Imports
from src import common

# Dependency Packages
#from comtypes.client import CreateObject

# Fetch the Queue commands
commandQ = common.requestQ


class Dispatcher(object):
    def __init__(self, udptransfor):
        # Setup TTS Engine
        self._engine = None
        self._stream = None
        self.udpserver = udptransfor
        #self.initialize_engine()

    #def initialize_engine(self):
        #self._engine = CreateObject("SAPI.SPVoice")
        #self._stream = CreateObject("SAPI.SpMemoryStream")
        #self._engine.AudioOutputStream = self._stream

    async def start(self):
        while True:
            # Wait for a command to come in
            command = await commandQ.get()

            try:
                # Fetch the method associated with the task
                method = getattr(self, command["task"])

                # Pass in any params if given
                if "params" in command:
                    result = method(**command["params"])
                else:
                    result = method()

            # Task method not found
            except AttributeError as e:
                print("invalid task: {}".format(command))
                print(e)
                result = dict(success=False, msg="invalid task: {}".format(e))

            # Some unexpected happend
            except Exception as e:
                print("Task failed: {}".format(e))
                result = dict(success=False, msg=str(e))

            # If no result was returned then set success to false
            if result is None:
                result = dict(success=False, msg="missing response")

            # Return a response if the client is expecting one
            if "id" in command:
                command["response"] = result
                command.pop("_client").send_data(command)

            # Mark task as done
            commandQ.task_done()


class TTS(Dispatcher):
    def speak(self, text, addr=None):
        """ Send text to tts engine and speak """
        print("Speak: {}".format(text))
        if addr is not None:
            self.udpserver.sendto(b"audio", tuple(addr))
        else:
            return dict(success=True, audio="audio")
        #self._engine.Speak(text)
        #return StringIO(bytearray(self._stream.GetData()))

    def stop(self):
        print("Stop:")
        #self._engine.Speak("", 3)
        return dict(success=True)

    def get_rate(self):
        """ Return the current speech rate """
        #rate = self._engine.Rate
        print("get rate:")
        return dict(success=True, rate=6)

    def set_rate(self, rate):
        """
        Change the speach rate of the voice

        :param rate: Rate to set the voice to
        :type rate: integer

        Rate must be between -10 and +10
        """
        print("set rate: {}".format(rate))
        if rate < -10 or rate > 10:
            raise ValueError("invalid rate {}".format(rate))
        else:
            #self._engine.Rate = rate
            return dict(success=True)

    def get_volume(self):
        """ Return the current volume level """
        print("get volume:")
        #volume = self._engine.Volume
        return dict(success=True, volume=100)

    def set_volume(self, volume):
        """
        Chagne the volume of the voice

        value : int --- level of the volume to change to
        """
        print("set volume: {}".format(volume))
        if volume < 0 or volume > 100:
            raise ValueError("invalid volume {}".format(volume))
        else:
            #self._engine.Volume = volume
            return dict(success=True)

    def get_voices(self):
        """ Return list of avalable voices as a Voice object """
        #voices = []
        #for voice in self._engine.GetVoices():
        #    voiceid = voice.Id
        #    name = voice.GetDescription()
        #    gender = voice.GetAttribute("Gender")
        #    voices.append(common.Voice(voiceid, name, gender))

        # Return a list of all available voices
        print("get voices:")
        return dict(success=True, voices=[common.Voice("voice id", "test voice", "male")])

    def get_voice(self):
        """ Return the current selected voice as a Voice object """
        #_voice = self._engine.Voice
        #voice = common.Voice(_voice.Id, _voice.GetDescription(), _voice.GetAttribute("Gender"))
        print("get voice:")
        voice = common.Voice("voice id", "test voice", "male")
        return dict(success=True, voice=voice)

    def set_voice(self, voiceobj):
        # Search all voices for given voiceid
        #for _voice in self._engine.GetVoices():
        #    if _voice.Id == voiceobj.voiceid:
        #        self._engine.Voice = _voice
        print("set voice: {}".format(voiceobj.name))
        return dict(success=True)
