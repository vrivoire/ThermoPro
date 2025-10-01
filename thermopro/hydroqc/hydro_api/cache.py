"""Custon cache module."""

import functools
from collections.abc import Callable
from typing import ParamSpec, TypeVar, cast

from aiocache import Cache, cached  # type: ignore

T = TypeVar("T")
P = ParamSpec("P")


class CCached(cached):  # type: ignore[misc]
    """Custom cache class based on aiocache."""

    def __init__(self, ttl: int) -> None:
        """Initialize custom cache decorator."""
        cached.__init__(self, ttl=ttl, cache=Cache.MEMORY)

    def __call__(self, func: Callable[P, T]) -> Callable[P, T]:
        """Call custom cache decorator."""
        self.cache = self._cache()

        @functools.wraps(func)
        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> T:
            value = await self.decorator(func, *args, **kwargs)
            return cast(T, value)

        wrapper.cache = self.cache  # type: ignore[attr-defined]
        return cast(Callable[P, T], wrapper)
