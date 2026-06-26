from abc import ABC, abstractmethod
from typing import Dict, Any, List
from result import Result


class UserRepository(ABC):

    @abstractmethod
    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_by_id(self, user_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def update(self, user_id: str, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def disable(self, user_id: str) -> Result[Dict[str, Any], str]:
        pass
