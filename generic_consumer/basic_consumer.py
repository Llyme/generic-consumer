from abc import ABC
import json
from signal import SIGTERM
from typing import Iterable
import zlib
from .generic_consumer import GenericConsumer
from .payload_preprocessor import PayloadPreprocessor


class BasicConsumer(GenericConsumer, ABC):
    """
    A simple implementation of a consumer that requires a payload.
    """

    log = True

    @classmethod
    def _payload_preprocessors(
        cls,
    ) -> Iterable[str]:
        """
        Transforms payloads before being processed.

        Use `generic_consumer.PayloadPreprocessor`
        """
        return []

    def _no_payloads(self):
        """
        Called if there are no available payloads.
        """
        return False

    def _has_payloads(self, payloads: list):
        """
        Called if there is at least 1 payload.
        """
        return True

    def __process_payload(self, payload):
        payload_preprocessors = self._payload_preprocessors()

        for cmd in payload_preprocessors:
            if cmd == PayloadPreprocessor.BYTES_DECODE:
                return payload.decode()

            if cmd == PayloadPreprocessor.JSON_LOADS:
                return json.loads(payload)

            if cmd == PayloadPreprocessor.ZLIB_DECOMPRESS:
                return zlib.decompress(payload)

            return self._custom_payload_preprocessor(cmd, payload)

        return payload

    def _custom_payload_preprocessor(self, cmd: str, payload):
        return payload

    def __try_json_payloads(self, payloads: list):
        if payloads == None:
            return None

        result = []
        ok = False

        for payload in payloads:
            try:
                result.append(self.__process_payload(payload))
                ok = True

            except Exception as e:
                print("Payload processing error!", e)

        return result if ok else None

    def _run(self, payloads):
        payloads = self.__try_json_payloads(payloads)

        if payloads == None:
            return self._no_payloads()

        count = len(payloads)
        queue_name = self.queue_name()

        if self.log:
            print(f"Got {count} payload(s) from '{queue_name}'.")

        return SIGTERM
