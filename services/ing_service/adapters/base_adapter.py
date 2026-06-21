
from abc import ABC, abstractmethod


class BaseAdapter(ABC):

    @abstractmethod
    def can_handle(self, event: dict) -> bool:
        pass

    @abstractmethod
    def transform(self, event: dict) -> dict:
        pass
