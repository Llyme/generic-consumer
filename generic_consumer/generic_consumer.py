from abc import ABC
import asyncio
import inspect
import re
from time import perf_counter
from typing import (
    Any,
    Callable,
    Iterable,
    List,
    Optional,
    Type,
    final,
)
from fun_things import (
    get_all_descendant_classes,
    categorizer,
    as_asyncgen,
    as_async,
    as_gen,
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
    def passive(cls):
        """
        Determines the consumer's significance in `start()`.

        See `start()` for more details.
        """
        return False

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
        The name of this consumer.

        You can override this by making a static/class method
        with the name `queue_name`.

        Can be asynchronous.

        Can be iterable.
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
    async def __first_queue_name(cls):
        value = as_asyncgen(cls.queue_name())

        return await value.__anext__()

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
    async def condition(cls, queue_name: str):
        """
        Must return `True` in order for this consumer to be selected.

        By default, this checks if the `queue_name` is the same
        as this consumer's `queue_name`.

        You can override this by making a static/class method
        with the name `condition`.

        Can be asynchronous.
        """
        async for queue_name0 in as_asyncgen(cls.queue_name()):
            if queue_name0 == queue_name:
                return True

        return False

    def init(self):
        """
        Called when `run()` is called.

        Can be asynchronous.

        Can be a generator.
        """
        pass

    def get_nested_consumers(self):
        """
        Return the nested consumers here.

        Can be non-iterable,
        which becomes an array with a single value.

        Can be asynchronous.

        Can be iterable.
        """
        pass

    def get_payloads(self):
        """
        Return the payloads here.

        Can be non-iterable,
        which becomes an array with a single value.

        Can be asynchronous.

        Can be iterable.
        """
        pass

    def payload_preprocessors(
        self,
    ) -> Iterable[Callable]:
        """
        Transforms payloads before being processed.

        Can be asynchronous.

        Can be iterable.
        """
        return []

    @final
    async def __preprocess_payload(self, payload):
        processed_payload = payload

        try:
            processors = as_asyncgen(self.payload_preprocessors())

            async for processor in processors:
                processed_payload = processor(processed_payload)

            return processed_payload

        except Exception as e:
            if self.log:
                logger.error(ERROR_PAYLOAD, e)

        return payload

    def process(self, payloads: list):
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

    def process_one(self, payload):
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
    async def __run(
        self,
        *args,
        **kwargs,
    ):
        queue_name = await self.__first_queue_name()

        self.__class__.__run_count += 1
        self.args = args
        self.kwargs = kwargs

        async for _ in as_asyncgen(self.init()):
            pass  # Only initializing.

        payloads = []
        payloads_count = 0

        async for payload in as_asyncgen(self.get_payloads()):
            payloads.append(
                await self.__preprocess_payload(payload),
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
            values = self.process_one(payload)
            values = as_asyncgen(
                values,
                lambda value: inspect.isgenerator(
                    value,
                )
                or inspect.isasyncgen(
                    value,
                ),
            )

            async for value in values:
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

        values = self.process(payloads)
        values = as_asyncgen(
            values,
            lambda value: inspect.isgenerator(
                value,
            )
            or inspect.isasyncgen(
                value,
            ),
        )

        async for value in values:
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
    async def run_async_all(self, *args, **kwargs):
        items = []

        async for item in self.__run_async(args, kwargs, False):
            items.append(item)

        return items

    @final
    async def __run_async(
        self,
        args: tuple,
        kwargs: dict,
        return_signals: bool,
    ):
        queue_name = await self.__first_queue_name()

        logger.debug(
            INFO_CONSUMER_START.format(
                queue_name=queue_name,
            ),
        )

        t1 = perf_counter()
        stop = False

        async for item in self.__run(*args, **kwargs):
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
    async def run_async(self, *args, **kwargs):
        """
        Ignores `max_run_count`.
        """
        async for item in self.__run_async(args, kwargs, False):
            yield item

    @final
    def run_all(self, *args, **kwargs):
        return [*self.run(*args, **kwargs)]

    @final
    def run(self, *args, **kwargs):
        """
        Ignores `max_run_count`.
        """
        return as_gen(self.__run_async(args, kwargs, False))

    @staticmethod
    @final
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
    async def get_consumer_async(cls, queue_name: str):
        consumers = cls.get_consumers_async(queue_name)

        async for consumer in consumers:
            return consumer

    @classmethod
    @final
    def get_consumer(cls, queue_name: str):
        """
        Returns the first consumer with the given `queue_name`
        and the highest priority number.
        """
        return asyncio.new_event_loop().run_until_complete(
            cls.get_consumer_async(queue_name),
        )

    @classmethod
    @final
    async def get_consumers_async(cls, queue_name: str):
        descendants = GenericConsumer.available_consumers()

        for descendant in descendants:
            if not descendant.enabled:
                continue

            ok = as_async(descendant.condition(queue_name))

            if not await ok:
                continue

            yield descendant()

    @classmethod
    @final
    def get_consumers(cls, queue_name: str):
        """
        Returns all consumers that has a
        satisfied `condition(queue_name)`,
        starting from the highest priority number.

        The consumers are instantiated while generating.
        """
        return as_gen(cls.get_consumers_async(queue_name))

    @classmethod
    @final
    async def start_all_async(
        cls,
        queue_name: str,
        print_consumers=True,
        print_indent=2,
        require_non_passive_consumer=True,
    ):
        items = []

        async for item in cls.start_async(
            queue_name,
            print_consumers,
            print_indent,
            require_non_passive_consumer,
        ):
            items.append(item)

        return items

    @classmethod
    @final
    async def start_async(
        cls,
        queue_name: str,
        print_consumers=True,
        print_indent=2,
        require_non_passive_consumer=True,
    ):
        consumers: List["GenericConsumer"] = []

        async for consumer in cls.get_consumers_async(queue_name):
            consumers.append(consumer)

        has_non_passive = map(
            lambda consumer: not consumer.passive(),
            consumers,
        )
        has_non_passive = any(has_non_passive)

        if print_consumers:
            await cls.print_available_consumers_async(
                queue_name,
                print_indent,
            )

            await cls.__print_load_order(
                consumers,
            )

        if require_non_passive_consumer and not has_non_passive:
            raise Exception(
                ERROR_NO_ACTIVE_CONSUMER.format(
                    queue_name=queue_name,
                ),
            )

        for consumer in consumers:
            queue_name = await consumer.__first_queue_name()

            if not consumer.enabled:
                logger.debug(
                    WARN_CONSUMER_DISABLED.format(
                        queue_name=queue_name,
                    ),
                )
                continue

            stop = False

            async for item in consumer.__run_async(
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
        return as_gen(
            cls.start_async(
                queue_name,
                print_consumers,
                print_indent,
                require_non_passive_consumer,
            ),
        )

    @staticmethod
    @final
    async def __print_load_order(
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
                consumer.priority_number(),
                await consumer.__first_queue_name(),
                consumer.passive(),
            )
            for consumer in consumers
        ]

        has_negative = consumers[-1].priority_number() < 0
        zfill = map(
            lambda consumer: consumer.priority_number(),
            consumers,
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
    async def __get_printed_queue_name(
        item: Type["GenericConsumer"],
        queue_name: Optional[str],
    ):
        text = await item.__first_queue_name()

        if queue_name == None:
            return text

        if not item.enabled:
            # Not enabled.
            text = chalk.dim.gray(text)
            text = f"{text} {chalk.bold('✕')}"

        elif not await as_async(item.condition(queue_name)):
            # Enabled, but condition is not met.
            text = chalk.dim.gray(text)

        elif item.passive():
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
    async def __draw_consumers(
        queue_name: str,
        consumers,
        indent_text: str,
    ):
        consumers0: List[Type["GenericConsumer"]] = [
            consumer[0] for consumer in consumers
        ]
        consumers0.sort(
            key=lambda consumer: consumer.priority_number(),
            reverse=True,
        )

        count = len(consumers0)
        priority_numbers = [
            *map(
                lambda consumer: consumer.priority_number(),
                consumers0,
            )
        ]
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

            priority_number = consumer.priority_number()

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
                await GenericConsumer.__get_printed_queue_name(
                    consumer,
                    queue_name,
                ),
            )

        print()

    @staticmethod
    @final
    async def __draw_categories(
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
            await GenericConsumer.__draw_consumers(
                queue_name=queue_name,
                consumers=category,
                indent_text=indent_text,
            )
            return

        for sub_category in category.items():
            yield indent_size + 1, sub_category

    @classmethod
    @final
    async def print_available_consumers_async(
        cls,
        queue_name: str = None,  # type: ignore
        indent: int = 2,
    ):
        consumers = filter(
            lambda consumer: not consumer.hidden(),
            cls.available_consumers(),
        )
        # categorized: List[Tuple[int, Tuple[str, Any]]] = []
        categorized = [
            (
                consumer,
                await consumer.__first_queue_name(),
            )
            for consumer in consumers
        ]
        categorized = categorizer(
            categorized,
            lambda tuple: tuple[1],
        )
        categorized = categorized.items()
        categorized = [(0, v) for v in categorized]

        while len(categorized) > 0:
            indent_size, (keyword, category) = categorized.pop()

            sub_categories = GenericConsumer.__draw_categories(
                queue_name=queue_name,
                indent_size=indent_size,
                indent_scale=indent,
                keyword=keyword,
                category=category,
            )

            async for sub_category in sub_categories:
                categorized.append(sub_category)

    @classmethod
    @final
    def print_available_consumers(
        cls,
        queue_name: str = None,  # type: ignore
        indent: int = 2,
    ):
        asyncio.new_event_loop().run_until_complete(
            cls.print_available_consumers_async(
                queue_name,
                indent,
            )
        )
