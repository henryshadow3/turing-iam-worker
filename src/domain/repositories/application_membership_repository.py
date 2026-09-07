from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from result import Result


class ApplicationMembershipRepository(ABC):

    @abstractmethod
    def list_all(self, user_id: Optional[str] = None,
                 tenant_application_id: Optional[str] = None) -> Result[List[Dict[str, Any]], str]:
        pass

    @abstractmethod
    def get_by_id(self, application_membership_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def create(self, data: Dict[str, Any]) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def update(self, application_membership_id: str, role_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def toggle(self, application_membership_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def toggle_by_application(self, user_id: str, application_id: str) -> Result[Dict[str, Any], str]:
        pass
