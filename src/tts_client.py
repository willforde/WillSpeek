# Standard library imports
import collections
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

    def _future_response(self, request):
        request["id"] = common.gen_random()
        future = common.responseF[request["id"]]
        self.client_con.send_data(request)
        result = self.loop.run_until_complete(future)
        del common.responseF[request["id"]]
        return result

    def get_rate(self):
        request = dict(task="get_rate")
        ret = self._future_response(request)
        return ret["rate"]

    def set_rate(self, rate):
        """
        Change the speach rate of the voice

        :param rate: Rate to set the voice to
        :type rate: integer

        :raises ValueError: If value is out of range

        .. note::
            Rate must be between -10 and +10
        """
        if rate < -10 or rate > 10:
            raise ValueError("invalid rate %s" % rate)

        request = dict(task="set_rate", rate=rate)
        ret = self._future_response(request)
        return ret["success"]

    def get_volume(self):
        request = dict(task="get_volume")
        ret = self._future_response(request)
        return ret["volume"]

    def set_volume(self, volume):
        if volume < 0 or volume > 100:
            raise ValueError("invalid volume %s" % volume)

        request = dict(task="set_volume", volume=volume)
        ret = self._future_response(request)
        return ret["success"]

    def get_voices(self):
        request = dict(task="get_voices")
        ret = self._future_response(request)
        return ret["voices"]

    def get_voice(self):
        request = dict(task="get_voice")
        return self._future_response(request)

    def set_voice(self, voice):
        request = dict(task="set_voice", voiceid=voice)
        ret = self._future_response(request)
        return ret["success"]
