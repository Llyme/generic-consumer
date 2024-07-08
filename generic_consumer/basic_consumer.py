from abc import ABC
from signal import SIGABRT
from typing import Any, Callable, Iterable, final
from .generic_consumer import GenericConsumer


class BasicConsumer(GenericConsumer, ABC):
    """
    A simple implementation of a consumer that requires a payload.
    """

    log = True
    run_one_by_one = False

    @classmethod
    def _payload_preprocessors(
        cls,
    ) -> Iterable[Callable[[Any], Any]]:
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
        callables = self._payload_preprocessors()

        for callable in callables:
            payload = callable(payload)

        return payload

    def __process_payloads(self, payloads: list):
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

    @final
    def _run(self, payloads):
        if self.run_one_by_one:
            return SIGABRT

        payloads = self.__process_payloads(payloads)

        if payloads == None:
            return self._no_payloads()

        count = len(payloads)
        queue_name = self.queue_name()

        if self.log:
            print(f"Got {count} payload(s) from '{queue_name}'.")

        return self._has_payloads(payloads)

    @final
    def _run_one(self, payload):
        try:
            return self.__process_payload(payload)

        except Exception as e:
            print("Payload processing error!", e)
