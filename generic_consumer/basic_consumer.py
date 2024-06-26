from abc import ABC
from typing import Any
from .generic_consumer import GenericConsumer


class BasicConsumer(GenericConsumer, ABC):
    """
    A simple implementation of a consumer that requires a payload.
    """

    log = True

    def _no_payloads(self) -> Any:
        return False

    def _has_payloads(self, payloads: list):
        return True

    def _run(self, payloads: list) -> Any:
        if payloads == None:
            return self._no_payloads()

        count = len(payloads)

        if count == 0:
            return self._no_payloads()

        if self.log:
            print(f"Got {count} payload(s).")

        return self._has_payloads(payloads)
