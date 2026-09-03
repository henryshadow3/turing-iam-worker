from abc import ABC, abstractmethod
from typing import Dict, Any, List
from result import Result


class ApplicationRepository(ABC):

    @abstractmethod
    def list_all(self) -> Result[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_by_id(self, application_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def toggle(self, application_id: str) -> Result[Dict[str, Any], str]:
        pass
