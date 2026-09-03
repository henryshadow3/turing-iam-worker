from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from result import Result


class TenantApplicationRouteRepository(ABC):

    @abstractmethod
    def list_all(self, tenant_application_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def update(self, route_id: str, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def toggle(self, route_id: str) -> Result[Dict[str, Any], str]:
        pass
