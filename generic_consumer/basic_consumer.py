from abc import ABC
import json
from typing import Any
from .generic_consumer import GenericConsumer


class BasicConsumer(GenericConsumer, ABC):
    """
    A simple implementation of a consumer that requires a payload.
    """

    log = True

    @classmethod
    def _payload_is_json(cls):
        """
        If the payload should be converted into a dictionary.
        """
        return False

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

    def __try_json_payloads(self, payloads: list):
        if payloads == None:
            return None

        if self._payload_is_json():
            return payloads

        result = []
        ok = False

        for payload in payloads:
            try:
                result.append(json.loads(payload))
                ok = True
            except:
                pass

        return result if ok else None

    def _run(self, payloads: list) -> Any:
        payloads = self.__try_json_payloads(payloads)  # type: ignore

        if payloads == None:
            return self._no_payloads()

        count = len(payloads)
        queue_name = self.queue_name()

        if self.log:
            print(f"Got {count} payload(s) from '{queue_name}'.")

        return self._has_payloads(payloads)
