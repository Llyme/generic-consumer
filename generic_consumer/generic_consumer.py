from abc import ABC
import asyncio
import inspect
import re
from time import perf_counter
from typing import (
    Any,
    Callable,
    Generator,
    Iterable,
    List,
    Optional,
    Type,
    final,
)
from fun_things import (
    get_all_descendant_classes,
    categorizer,
    as_gen,
    as_sync,
)
from simple_chalk import chalk

from .signal import Signal

from .strings import *
from .logger import logger


class GenericConsumer(ABC):
    enabled = True
    """
    If this consumer is enabled for activation.
    """
    log = True
    """
    If the consumer should print logs.
    """
    process_empty_payloads = False
    """
    If the consumer should still process
    even if there are no payloads.

    `process_one` will not be called
    even if this is `True`.
    """
    __run_count = 0

    @classmethod
    @final
    def get_run_count(cls):
        """
        The amount of times this consumer has run.
        """
        return cls.__run_count

    @classmethod
    def passive(cls) -> bool:
        """
        Determines the consumer's significance in `start()`.

        See `start()` for more details.
        """
        return False

    @classmethod
    @final
    def __passive(cls):
        return as_sync(cls.passive())

    @classmethod
    def hidden(cls) -> bool:
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
    @final
    def __hidden(cls):
        return as_sync(cls.hidden())

    @classmethod
    def max_run_count(cls) -> int:
        """
        The number of times this consumer can be called.

        At 0 or less,
        this consumer can be called at any number of times.

        You can override this by making a static/class method
        with the name `run_once`.
        """
        return 0

    @classmethod
    @final
    def __max_run_count(cls):
        return as_sync(cls.max_run_count())

    @classmethod
    def queue_name(cls):
        """
        The name of this consumer.

        You can override this by making a static/class method
        with the name `queue_name`.

        Can be asynchronous.

        Can be a generator.
        """
        return re.sub(
            # 1;
            # Look for an uppercase after a lowercase.
            # HelloWorld = HELLO_WORLD
            # 2;
            # Look for an uppercase followed by a lowercase,
            # after an uppercase or a number.
            # Example; HELLOWorld = HELLO_WORLD
            # 3;
            # Look for a number after a letter.
            # Example; HelloWorld1 = HELLO_WORLD_1
            r"(?<=[a-z])(?=[A-Z0-9])|(?<=[A-Z0-9])(?=[A-Z][a-z])|(?<=[A-Za-z])(?=\d)",
            "_",
            cls.__name__,
        ).upper()

    @classmethod
    @final
    def __queue_name(cls):
        return as_gen(cls.queue_name())

    @classmethod
    @final
    def __first_queue_name(cls) -> str:  # type: ignore
        for queue_name in cls.__queue_name():
            return queue_name

    @classmethod
    def priority_number(cls) -> float:
        """
        If there are multiple consumers that
        have satisfied conditions,
        the highest priority number goes first.

        You can override this by making a static/class method
        with the name `priority_number`.
        """
        return 0

    @classmethod
    @final
    def __priority_number(cls):
        return as_sync(cls.priority_number())

    @classmethod
    def condition(cls, queue_name: str):
        """
        Must return `True` in order for this consumer to be selected.

        By default, this checks if the `queue_name` is the same
        as this consumer's `queue_name`.

        You can override this by making a static/class method
        with the name `condition`.

        Can be asynchronous.
        """
        return queue_name in cls.__queue_name()

    @classmethod
    @final
    def __condition(cls, queue_name: str):
        return as_sync(cls.condition(queue_name))

    def init(self):
        """
        Called when `run()` is called.

        Can be asynchronous.

        Can be a generator.
        """
        pass

    @final
    def __init(self):
        for _ in as_gen(self.init()):
            pass

    def get_payloads(self) -> Any:
        """
        Return the payloads here.

        Can be non-iterable,
        which becomes an array with a single value.

        Can be asynchronous.

        Can be iterable.
        """
        pass

    @final
    def __get_payloads(self) -> Generator[Any, Any, Any]:
        payloads = self.get_payloads()

        if inspect.isawaitable(payloads):
            payloads = asyncio.run(payloads)  # type: ignore

        if inspect.isasyncgen(payloads):
            while True:
                try:
                    yield asyncio.run(payloads.__anext__())

                except StopAsyncIteration:
                    return

        if isinstance(payloads, str):
            yield payloads
            return

        if isinstance(payloads, bytes):
            yield payloads
            return

        if isinstance(payloads, Iterable):
            for payload in payloads:
                yield payload

            return

        yield payloads

    def payload_preprocessors(self) -> Any:
        """
        Transforms payloads before being processed.

        Can be asynchronous.

        Can be iterable.
        """
        pass

    @final
    def __payload_preprocessors(
        self,
    ) -> Generator[
        Callable,
        Any,
        Any,
    ]:
        preprocessors = self.payload_preprocessors()

        if inspect.isawaitable(preprocessors):
            preprocessors = asyncio.run(preprocessors)  # type: ignore

        if inspect.isasyncgen(preprocessors):
            while True:
                try:
                    yield asyncio.run(preprocessors.__anext__())

                except StopAsyncIteration:
                    return

        if isinstance(preprocessors, Iterable):
            for preprocessor in preprocessors:
                yield preprocessor

            return

        yield preprocessors  # type: ignore

    @final
    def __preprocess_payload(self, payload):
        processed_payload = payload

        try:
            processors = self.__payload_preprocessors()

            for processor in processors:
                if processor == None:
                    continue

                processed_payload = as_sync(
                    processor(processed_payload),
                )

            return processed_payload

        except Exception as e:
            if self.log:
                logger.error(ERROR_PAYLOAD, e)

        return payload

    def process(self, payloads: list) -> Any:
        """
        Processes all of the payloads.

        Return `Signal.BREAK`
        to stop.

        Return `Signal.INTERRUPT`
        to prevent the next processes.

        Return `Signal.TERMINATE`
        to stop the entire process.
        """
        return Signal.BREAK

    @final
    def __process(self, payloads: list):
        return as_gen(self.process(payloads))

    def process_one(self, payload) -> Any:
        """
        Processes payloads 1 by 1.

        Return `Signal.BREAK`
        to stop.

        Return `Signal.INTERRUPT`
        to prevent the next processes.

        Return `Signal.TERMINATE`
        to stop the entire process.
        """
        return Signal.BREAK

    @final
    def __process_one(self, payload):
        return as_gen(self.process_one(payload))

    @final
    def __run_internal(
        self,
        *args,
        **kwargs,
    ):
        queue_name = self.__first_queue_name()

        self.__class__.__run_count += 1
        self.args = args
        self.kwargs = kwargs

        self.__init()

        payloads = []
        payloads_count = 0

        for payload in self.__get_payloads():
            payloads.append(
                self.__preprocess_payload(payload),
            )
            payloads_count += 1

        if not self.process_empty_payloads and payloads_count == 0:
            return

        if self.log and payloads_count > 0:
            logger.info(
                INFO_PAYLOAD.format(
                    count=payloads_count,
                    queue_name=queue_name,
                )
            )

        for payload in payloads:
            stop = False

            for value in self.__process_one(payload):
                if value == Signal.CONTINUE:
                    continue

                if value == Signal.BREAK:
                    break

                if value == Signal.INTERRUPT:
                    stop = True
                    break

                if value == Signal.TERMINATE:
                    yield Signal.TERMINATE
                    return

                yield value

            if stop:
                break

        for value in self.__process(payloads):
            if value == Signal.CONTINUE:
                continue

            if value == Signal.BREAK:
                break

            if value == Signal.INTERRUPT:
                break

            if value == Signal.TERMINATE:
                yield Signal.TERMINATE
                return

            yield value

    @final
    def run_all(self, *args, **kwargs):
        return [*self.__run(args, kwargs, False)]

    @final
    def __run(
        self,
        args: tuple,
        kwargs: dict,
        return_signals: bool,
    ):
        queue_name = self.__first_queue_name()

        logger.debug(
            INFO_CONSUMER_START.format(
                queue_name=queue_name,
            ),
        )

        t1 = perf_counter()
        stop = False

        for item in self.__run_internal(*args, **kwargs):
            if item == Signal.TERMINATE:
                stop = True
                break

            yield item

        t2 = perf_counter()

        logger.debug(
            INFO_CONSUMER_END.format(
                queue_name=queue_name,
                duration=t2 - t1,
            )
        )

        if return_signals and stop:
            yield Signal.TERMINATE

    @final
    def run(self, *args, **kwargs):
        """
        Ignores `max_run_count`.
        """
        for item in self.__run(args, kwargs, False):
            yield item

    @staticmethod
    @final
    def __consumer_predicate(consumer: Type["GenericConsumer"]):
        max_run_count = consumer.__max_run_count()

        if max_run_count <= 0:
            return True

        return consumer.__run_count < max_run_count

    @classmethod
    @final
    def available_consumers(cls):
        """
        All consumers sorted by highest priority number.
        """
        return sorted(
            [
                descendant
                for descendant in get_all_descendant_classes(
                    cls,
                    exclude=[ABC],
                )
                if GenericConsumer.__consumer_predicate(descendant)
            ],
            key=lambda descendant: descendant.__priority_number(),
            reverse=True,
        )

    @classmethod
    @final
    def get_consumer(cls, queue_name: str):
        """
        Returns the first consumer with the given `queue_name`
        and the highest priority number.
        """
        for consumer in cls.get_consumers(queue_name):
            return consumer

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
            if not descendant.enabled:
                continue

            ok = descendant.__condition(queue_name)

            if not ok:
                continue

            yield descendant()

    @classmethod
    @final
    def start_all(
        cls,
        queue_name: str,
        print_consumers=True,
        print_indent=2,
        require_non_passive_consumer=True,
    ):
        return [
            *cls.start(
                queue_name,
                print_consumers,
                print_indent,
                require_non_passive_consumer,
            )
        ]

    @classmethod
    @final
    def start(
        cls,
        queue_name: str,
        print_consumers=True,
        print_indent=2,
        require_non_passive_consumer=True,
    ):
        """
        Requires at least 1 non-passive consumer to be selected.
        """
        consumers = [*cls.get_consumers(queue_name)]
        has_non_passive = any(not consumer.__passive() for consumer in consumers)

        if print_consumers:
            cls.print_available_consumers(
                queue_name,
                print_indent,
            )

            cls.__print_load_order(
                consumers,
            )

        if require_non_passive_consumer and not has_non_passive:
            raise Exception(
                ERROR_NO_ACTIVE_CONSUMER.format(
                    queue_name=queue_name,
                ),
            )

        for consumer in consumers:
            queue_name = consumer.__first_queue_name()

            if not consumer.enabled:
                logger.debug(
                    WARN_CONSUMER_DISABLED.format(
                        queue_name=queue_name,
                    ),
                )
                continue

            stop = False

            for item in consumer.__run(
                (),
                {},
                True,
            ):
                if item == Signal.TERMINATE:
                    stop = True
                    break

                yield item

            if stop:
                break

    @staticmethod
    @final
    def __print_load_order(
        consumers: List["GenericConsumer"],
    ):
        if not any(consumers):
            return

        print(
            f"<{chalk.yellow('Load Order')}>",
            chalk.yellow.bold("↓"),
        )

        items = [
            (
                consumer.__priority_number(),
                consumer.__first_queue_name(),
                consumer.__passive(),
            )
            for consumer in consumers
        ]

        has_negative = items[-1][0] < 0
        zfill = map(
            lambda item: item[0],
            items,
        )
        zfill = map(lambda number: len(str(abs(number))), zfill)
        zfill = max(zfill)

        if has_negative:
            zfill += 1

        for priority_number, queue_name, passive in items:
            if has_negative:
                priority_number = "%+d" % priority_number
            else:
                priority_number = str(priority_number)

            priority_number = priority_number.zfill(zfill)

            if passive:
                queue_name = chalk.blue.bold(queue_name)
            else:
                queue_name = chalk.green.bold(queue_name)

            print(
                f"[{chalk.yellow(priority_number)}]",
                chalk.green(queue_name),
            )

        print()

    @staticmethod
    @final
    def __get_printed_queue_name(
        item: Type["GenericConsumer"],
        queue_name: Optional[str],
    ):
        text = item.__first_queue_name()

        if queue_name == None:
            return text

        if not item.enabled:
            # Not enabled.
            text = chalk.dim.gray(text)
            text = f"{text} {chalk.bold('✕')}"

        elif not item.__condition(queue_name):
            # Enabled, but condition is not met.
            text = chalk.dim.gray(text)

        elif item.__passive():
            # Passive consumer.
            text = chalk.blue.bold(text)
            text = f"{text} {chalk.bold('✓')}"

        else:
            # Non-passive (active) consumer.
            text = chalk.green.bold(text)
            text = f"{text} {chalk.bold('✓')}"

        return text

    @staticmethod
    @final
    def __draw_consumers(
        queue_name: str,
        consumers,
        indent_text: str,
    ):
        consumers0: List[Type["GenericConsumer"]] = [
            consumer[0] for consumer in consumers
        ]
        consumers0.sort(
            key=lambda consumer: consumer.__priority_number(),
            reverse=True,
        )

        count = len(consumers0)
        priority_numbers = [consumer.__priority_number() for consumer in consumers0]
        max_priority_len = map(
            lambda number: len(str(abs(number))),
            priority_numbers,
        )
        max_priority_len = max(max_priority_len)
        has_negative = map(
            lambda number: number < 0,
            priority_numbers,
        )
        has_negative = any(has_negative)

        if has_negative:
            max_priority_len += 1

        for consumer in consumers0:
            count -= 1

            priority_number = consumer.__priority_number()

            if has_negative:
                priority_number = "%+d" % priority_number
            else:
                priority_number = str(priority_number)

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
    @final
    def __draw_categories(
        queue_name: str,
        indent_size: int,
        indent_scale: int,
        keyword: str,
        category: Any,
    ):
        if keyword == None:
            keyword = "*"

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
        categorized = [
            (0, pair)
            for pair in categorizer(
                [
                    (
                        consumer,
                        consumer.__first_queue_name(),
                    )
                    for consumer in filter(
                        lambda consumer: not consumer.__hidden(),
                        cls.available_consumers(),
                    )
                ],
                lambda tuple: tuple[1],
            ).items()
        ]

        while len(categorized) > 0:
            indent_size, (keyword, category) = categorized.pop()

            for sub_category in GenericConsumer.__draw_categories(
                queue_name=queue_name,
                indent_size=indent_size,
                indent_scale=indent,
                keyword=keyword,
                category=category,
            ):
                categorized.append(sub_category)
