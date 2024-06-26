from abc import ABC


class PassiveConsumer(ABC):
    """
    A simple implementation of a consumer that is always called
    and will only run once.
    """

    @classmethod
    def hidden(cls):
        return True

    @classmethod
    def max_run_count(cls):
        return 1

    @classmethod
    def priority_number(cls):
        return 100

    @classmethod
    def condition(cls, queue_name: str):
        return True
