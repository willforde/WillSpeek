# Standard library imports
import asyncio

# Package imports
from src import monitors
from src import common


class TTS(object):
    def __init__(self, loop, send_data, udp_addr):
        self.send_data = send_data
        self.loop = loop

        # Setup autospeak to send all speach requests to server automatically
        core = self._autospeak(monitors.speakQ, udp_addr)
        asyncio.ensure_future(core)

    async def _autospeak(self, queue, udp_addr):
        while True:
            request = dict(task="speak", params={"addr": udp_addr})
            request["params"]["text"] = await queue.get()
            self.send_data(request)
            queue.task_done()

    async def _future_response(self, request):
        request["id"] = common.gen_random()
        future = common.responseF[request["id"]]
        self.send_data(request)
        try:
            result = await asyncio.wait_for(future, timeout=60)
        except asyncio.TimeoutError as e:
            result = dict(success=False, msg=str(e))
        finally:
            del common.responseF[request["id"]]

        if result.get("success", True) is False:
            print("Failed Response: {}".format(result))

        return result

    async def get_rate(self):
        request = dict(task="get_rate")
        ret = await self._future_response(request)
        if ret["success"]:
            return ret["rate"]
        else:
            return False

    async def set_rate(self, rate):
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

        request = dict(task="set_rate", params={"rate": rate})
        ret = await self._future_response(request)
        return ret["success"]

    async def get_volume(self):
        request = dict(task="get_volume")
        ret = await self._future_response(request)
        if ret["success"]:
            return ret["volume"]
        else:
            return False

    async def set_volume(self, volume):
        if volume < 0 or volume > 100:
            raise ValueError("invalid volume %s" % volume)

        request = dict(task="set_volume", params={"volume": volume})
        ret = await self._future_response(request)
        return ret["success"]

    async def get_voices(self):
        request = dict(task="get_voices")
        ret = await self._future_response(request)
        if ret["success"]:
            return ret["voices"]
        else:
            return False

    async def get_voice(self):
        request = dict(task="get_voice")
        ret = await self._future_response(request)
        if ret["success"]:
            return ret["voice"]
        else:
            return False

    async def set_voice(self, voice):
        request = dict(task="set_voice", params={"voiceobj": voice})
        ret = await self._future_response(request)
        return ret["success"]
