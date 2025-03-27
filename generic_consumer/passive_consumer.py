from abc import ABC

from .generic_consumer import GenericConsumer


class PassiveConsumer(GenericConsumer, ABC):
    """
    A simple implementation of a consumer that is always called
    and will only run once.
    """

    log = False
    process_empty_payloads = True

    @classmethod
    def passive(cls) -> bool:
        return True

    @classmethod
    def max_run_count(cls) -> int:
        return 1

    @classmethod
    def priority_number(cls) -> float:
        return 100

    @classmethod
    def condition(cls, queue_name: str) -> bool:
        return True
