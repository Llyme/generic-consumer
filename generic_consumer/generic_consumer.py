from abc import ABC
import re
from typing import Any, List, Tuple, final
from fun_things import get_all_descendant_classes, categorizer
from simple_chalk import chalk


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

        You can override this by making a static/class method
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

    @classmethod
    def priority_number(cls):
        """
        If there are multiple consumers with the same queue,
        the highest priority number goes first.

        You can override this by making a static/class method
        with the name `priority_number`.
        """
        return 0

    @classmethod
    def condition(cls, queue_name: str):
        """
        Must return `True` in order for this consumer to be selected.

        By default, this checks if the `queue_name` is the same
        as this consumer's `queue_name`.

        You can override this by making a static/class method
        with the name `condition`.
        """
        return cls.queue_name() == queue_name

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

    @classmethod
    @final
    def available_consumers(cls):
        """
        All consumers sorted by highest priority number.
        """
        descendants = get_all_descendant_classes(
            cls,
            exclude=[ABC],
        )

        return sorted(
            descendants,
            key=lambda descendant: descendant.priority_number(),
            reverse=True,
        )

    @classmethod
    @final
    def get_consumer(cls, queue_name: str):
        """
        Returns the first consumer with the given `queue_name`
        and the highest priority number.
        """
        descendants = cls.get_consumers(queue_name)

        for descendant in descendants:
            return descendant

    @classmethod
    @final
    def get_consumers(cls, queue_name: str):
        """
        Returns all consumers that has a
        satisfied `condition(queue_name)`,
        starting from the highest priority number.
        """
        descendants = GenericConsumer.available_consumers()

        for descendant in descendants:
            if descendant.condition(queue_name):
                yield descendant()

    @classmethod
    @final
    def print_available_consumers(
        cls,
        queue_name: str = None,  # type: ignore
        indent: int = 2,
    ):
        queue_names = map(
            lambda consumer: consumer.queue_name(),
            cls.available_consumers(),
        )
        categories: List[Tuple[int, Tuple[str, Any]]] = list(
            map(
                lambda v: (0, v),
                categorizer(queue_names).items(),
            )
        )

        while len(categories) > 0:
            indent_size, (keyword, category) = categories.pop()
            indent_text = " " * indent_size * indent

            print(
                f"{indent_text}{chalk.yellow(keyword)}:",
            )

            if isinstance(category, list):
                count = len(category)

                for item in category:
                    count -= 1

                    if queue_name != None:
                        if item == queue_name:
                            item = f"{chalk.green(item)} <--"
                        else:
                            item = chalk.red(item)

                    line = "├" if count > 0 else "└"
                    print(
                        f"{indent_text}{line}",
                        item,
                    )

                print()
                continue

            for sub_category in category.items():
                categories.append((indent_size + 1, sub_category))
