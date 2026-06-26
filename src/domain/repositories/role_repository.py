from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from result import Result


class RoleRepository(ABC):

    @abstractmethod
    def list_by_tenant(self, tenant_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_by_id(self, role_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        pass
