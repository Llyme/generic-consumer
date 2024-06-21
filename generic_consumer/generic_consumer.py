from abc import ABC
import re
from typing import Any, final
from fun_things import get_all_descendant_classes


class GenericConsumer(ABC):
    def _init(self):
        """
        Called when `run()` is called.
        """
        pass

    @classmethod
    def queue_name(cls):
        """
        Generic naming for queue names.

        You can change this by making a static/class method
        with the name `queue_name`.
        """
        return re.sub(
            # 1;
            # Look for an uppercase after a lowercase.
            # 2;
            # Look for an uppercase followed by a lowercase,
            # after an uppercase or a number.
            # 3;
            # Look for a number after a letter.
            r"(?<=[a-z])(?=[A-Z0-9])|(?<=[A-Z0-9])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=\d)",
            "_",
            cls.__name__,
        ).upper()

    def _get_payloads(self) -> list:  # type: ignore
        pass

    def _run(self, payloads: list) -> Any:
        pass

    @final
    def run(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs

        self._init()

        payloads = self._get_payloads() or []

        return self._run(payloads)

    @staticmethod
    @final
    def available_consumers():
        descendants = get_all_descendant_classes(
            GenericConsumer,
            exclude=[ABC],
        )

        for descendant in descendants:
            yield descendant

    @staticmethod
    @final
    def get_consumer(queue_name: str):
        descendants = GenericConsumer.get_consumers(queue_name)

        for descendant in descendants:
            return descendant

    @staticmethod
    @final
    def get_consumers(queue_name: str):
        descendants = GenericConsumer.available_consumers()

        for descendant in descendants:
            if descendant.queue_name() == queue_name:
                yield descendant()
