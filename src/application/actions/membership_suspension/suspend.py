import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def membership_suspend_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """iam.user.suspend_membership.in — interruptor global de membresía (W11,
    T-SP4-T2-I1). Desactiva TODAS las afiliaciones (turing.user_memberships)
    y accesos (turing.application_memberships) activos de un usuario de un
    jalón, guardando snapshot en turing.membership_suspensions para poder
    restaurar exactamente ese estado (ver
    MembershipSuspensionPostgresRepository.suspend). NO toca
    turing.users.is_active -- distinto del mecanismo ya existente que impide
    el login por completo.
    """
    try:
        user_id = data.get("user_id")
        if not user_id:
            return Err("MISSING_FIELD_USER_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.MEMBERSHIP_SUSPENSION, sql_session)
            result = repo.suspend(user_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"membership_suspend_action error: {e}")
        return Err(str(e))
