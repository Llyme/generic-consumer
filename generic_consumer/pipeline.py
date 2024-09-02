from abc import ABC

from .generic_consumer import GenericConsumer


class Pipeline(GenericConsumer, ABC):
    """
    A simple implementation of a consumer
    transformed into a pipeline architecture.
    """

    log = False
    enabled = False
    process_empty_payloads = True

    @classmethod
    def condition(cls, queue_name: str):
        return False
