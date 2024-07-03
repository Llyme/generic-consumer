from abc import ABC
import json
from signal import SIGTERM
from typing import Any, Iterable, Literal, Union
import zlib
from .generic_consumer import GenericConsumer


PayloadPreprocessor = Union[
    Literal["ZLIB_DECOMPRESS"],
    Literal["JSON_LOADS"],
    Literal["BYTES_DECODE"],
]


class BasicConsumer(GenericConsumer, ABC):
    """
    A simple implementation of a consumer that requires a payload.
    """

    log = True

    @classmethod
    def _payload_preprocessors(
        cls,
    ) -> Iterable[PayloadPreprocessor]:
        """
        Transforms payloads before being processed.
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
            if cmd == "BYTES_DECODE":
                return payload.decode()

            if cmd == "JSON_LOADS":
                return json.loads(payload)

            if cmd == "ZLIB_DECOMPRESS":
                return zlib.decompress(payload)

            raise Exception(
                f"Unknown payload preprocessor '{cmd}'!",
            )

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
