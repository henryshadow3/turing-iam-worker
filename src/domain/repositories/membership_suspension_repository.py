from abc import ABC, abstractmethod
from typing import Dict, Any
from result import Result


class MembershipSuspensionRepository(ABC):
    """Interruptor global de membresía (W11, T-SP4-T2-I1). Ver
    [[iam-worker-proto-passthrough-pattern]] y
    turing.membership_suspensions (migración 019 en db-turing).
    """

    @abstractmethod
    def suspend(self, user_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def restore(self, user_id: str) -> Result[Dict[str, Any], str]:
        pass

    @abstractmethod
    def status(self, user_id: str) -> Result[Dict[str, Any], str]:
        pass
