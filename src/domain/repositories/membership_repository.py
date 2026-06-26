from abc import ABC, abstractmethod
from typing import Dict, Any, List
from result import Result


class MembershipRepository(ABC):

    @abstractmethod
    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def delete(self, membership_id: str) -> Result[Dict[str, Any], str]:
        pass
