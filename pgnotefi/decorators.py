import asyncio
import contextlib
import logging
import typing

import typing_extensions

from pgnotefi import strategies, utils

P = typing_extensions.ParamSpec("P")
T = typing.TypeVar("T")


def cache(
    strategy: strategies.Strategy,
    statistics_callback: typing.Callable[[typing.Literal["hit", "miss"]], None] | None = None,
) -> typing.Callable[
    [typing.Callable[P, typing.Awaitable[T]]],
    typing.Callable[P, typing.Awaitable[T]],
]:
    def outer(
        fn: typing.Callable[P, typing.Awaitable[T]]
    ) -> typing.Callable[P, typing.Awaitable[T]]:
        cached = dict[typing.Hashable, asyncio.Future[T]]()

        async def inner(*args: P.args, **kw: P.kwargs) -> T:
            key = utils.make_key(args, kw)

            # If db-conn is down, disable cache.
            if not strategy.pg_connection_healthy():
                logging.warning("Database connection is closed, cache disabled.")
                return await fn(*args, **kw)

            # Clear cache if we have a event from
            # the database the instructs us to clear.
            if strategy.clear():
                logging.debug("Cache clear")
                cached.clear()

            # Cache hit
            with contextlib.suppress(KeyError):
                result = await cached[key]
                if statistics_callback:
                    statistics_callback("hit")
                return result

            with contextlib.suppress(KeyError):
                logging.debug("Cache hit")

            if statistics_callback:
                statistics_callback("miss")

            # By using a future as placeholder we avoid
            # cache stampeded. Note that on the "miss" branch/path, controll
            # is never given to the eventloopscheduler before the future
            # is create.
            cached[key] = waiter = asyncio.Future[T]()
            try:
                result = await fn(*args, **kw)
            except Exception as e:
                cached.pop(key, None)  # Next try should not result in a repeating exception
                waiter.set_exception(e)  # Propegate exception to other callers who are waiting.
                raise e from None  # Propegate exception to first caller.
            else:
                waiter.set_result(result)

            return result

        return inner

    return outer
