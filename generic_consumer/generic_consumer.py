from abc import ABC
import re
from typing import Any, List, Optional, Tuple, Type, final
from fun_things import get_all_descendant_classes, categorizer
from simple_chalk import chalk


class GenericConsumer(ABC):
    __run_count = 0

    def _init(self):
        """
        Called when `run()` is called.
        """
        pass

    @classmethod
    def hidden(cls):
        """
        If this consumer should not be displayed when printing
        available consumers.

        Hidden consumers are still called
        if they have a satisfied condition.

        You can override this by making a static/class method
        with the name `hidden`.
        """
        return False

    @classmethod
    def max_run_count(cls):
        """
        The number of times this consumer can be called.

        At 0 or less,
        this consumer can be called at any number of times.

        You can override this by making a static/class method
        with the name `run_once`.
        """
        return 0

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
        If there are multiple consumers that
        have satisfied conditions,
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
        """
        Ignores `max_run_count`.
        """
        self.__class__.__run_count += 1
        self.args = args
        self.kwargs = kwargs

        self._init()

        payloads = self._get_payloads() or []

        return self._run(payloads)

    @staticmethod
    def __consumer_predicate(consumer: Type["GenericConsumer"]):
        max_run_count = consumer.max_run_count()

        if max_run_count <= 0:
            return True

        return consumer.__run_count < max_run_count

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
        descendants = filter(
            GenericConsumer.__consumer_predicate,
            descendants,
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

        The consumers are instantiated while generating.
        """
        descendants = GenericConsumer.available_consumers()

        for descendant in descendants:
            if descendant.condition(queue_name):
                yield descendant()

    @classmethod
    @final
    def start(
        cls,
        queue_name: str,
        print_consumers: bool = True,
        print_indent: int = 2,
        error_when_empty: bool = True,
    ):
        consumers = [*cls.get_consumers(queue_name)]
        result = []

        if print_consumers:
            cls.print_available_consumers(
                queue_name,
                print_indent,
            )

            print(
                f"<{chalk.yellow('Load Order')}>",
                chalk.yellow("↓"),
            )

            items = map(
                lambda consumer: (
                    str(consumer.priority_number()),
                    consumer.queue_name(),
                ),
                consumers,
            )

            zfill = None

            for priority_number, queue_name in items:
                if zfill == None:
                    zfill = len(priority_number)

                priority_number = priority_number.zfill(zfill)
                print(
                    f"[{chalk.yellow(priority_number)}]",
                    chalk.green(queue_name),
                )

            print()

        for consumer in consumers:
            result.append(consumer.run())

        if error_when_empty and len(result) == 0:
            raise Exception(f"Unknown queue '{queue_name}'!")

        return result

    @staticmethod
    def __get_printed_queue_name(
        item: Type["GenericConsumer"],
        queue_name: Optional[str],
    ):
        item_queue_name = item.queue_name()

        if queue_name == None:
            return item_queue_name

        if item.condition(queue_name):
            return f"{chalk.green(item_queue_name)} <--"

        return chalk.red(item_queue_name)

    @staticmethod
    def __draw_consumers(
        queue_name: str,
        consumers: List[Type["GenericConsumer"]],
        indent_text: str,
    ):
        count = len(consumers)
        max_priority_len = map(
            lambda consumer: consumer.priority_number(),
            consumers,
        )
        max_priority_len = max(max_priority_len)
        max_priority_len = abs(max_priority_len)
        max_priority_len = str(max_priority_len)
        max_priority_len = len(max_priority_len)

        for consumer in consumers:
            count -= 1
            priority_number = str(consumer.priority_number())
            priority_number = priority_number.zfill(
                max_priority_len,
            )
            line = "├" if count > 0 else "└"

            print(
                f"{indent_text}{line}",
                f"[{chalk.yellow(priority_number)}]",
                GenericConsumer.__get_printed_queue_name(
                    consumer,
                    queue_name,
                ),
            )

        print()

    @staticmethod
    def __draw_categories(
        queue_name: str,
        indent_size: int,
        indent_scale: int,
        keyword: str,
        category: Any,
    ):
        indent_text = " " * indent_size * indent_scale

        print(f"{indent_text}{chalk.yellow(keyword)}:")

        if isinstance(category, list):
            GenericConsumer.__draw_consumers(
                queue_name=queue_name,
                consumers=category,
                indent_text=indent_text,
            )
            return

        for sub_category in category.items():
            yield indent_size + 1, sub_category

    @classmethod
    @final
    def print_available_consumers(
        cls,
        queue_name: str = None,  # type: ignore
        indent: int = 2,
    ):
        consumers = filter(
            lambda consumer: not consumer.hidden(),
            cls.available_consumers(),
        )
        categorized: List[Tuple[int, Tuple[str, Any]]] = list(
            map(
                lambda consumer: (0, consumer),
                categorizer(
                    consumers,
                    lambda consumer: consumer.queue_name(),
                ).items(),
            )
        )

        while len(categorized) > 0:
            indent_size, (keyword, category) = categorized.pop()

            sub_categories = GenericConsumer.__draw_categories(
                queue_name=queue_name,
                indent_size=indent_size,
                indent_scale=indent,
                keyword=keyword,
                category=category,
            )

            for sub_category in sub_categories:
                categorized.append(sub_category)
