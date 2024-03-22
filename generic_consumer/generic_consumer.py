from abc import abstractmethod
from typing import final


class GenericConsumer:
    @final
    def __init__(self, *args, **kwargs):
        self.payloads: list = None  # type: ignore
        self.__args = args
        self.__kwargs = kwargs

        self._initialize(*args, **kwargs)

    @abstractmethod
    def _initialize(self, *args, **kwargs):
        pass

    @abstractmethod
    def _has_payload(self, *args, **kwargs) -> bool:
        return True

    @abstractmethod
    def _get_payloads(self, *args, **kwargs) -> list:
        return []

    @abstractmethod
    def _run(self, *args, **kwargs):
        pass

    @final
    def run(self, *args, **kwargs) -> any:
        if self._has_payload():
            self.payloads = self._get_payloads(
                *self.__args,
                *args,
                **{
                    **self.__kwargs,
                    **kwargs,
                },
            )

        return self._run(
            *self.__args,
            *args,
            **{
                **self.__kwargs,
                **kwargs,
            },
        )
