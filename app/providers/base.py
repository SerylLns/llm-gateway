from abc import ABC, abstractmethod


class BaseProvider(ABC):
    @abstractmethod
    async def complete(
        self, messages: list[dict], temperature: float = 0.3
    ) -> dict:
        """Returns {"content": str, "tokens_in": int, "tokens_out": int}"""
        ...
