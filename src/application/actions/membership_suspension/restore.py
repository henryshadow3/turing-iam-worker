import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def membership_restore_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """iam.user.restore_membership.in — reactiva EXACTAMENTE las filas
    capturadas en el snapshot de la suspensión global vigente (W11,
    T-SP4-T2-I1) -- nunca "todas las filas del usuario", solo las listadas
    en turing.membership_suspensions. Ver
    MembershipSuspensionPostgresRepository.restore.
    """
    try:
        user_id = data.get("user_id")
        if not user_id:
            return Err("MISSING_FIELD_USER_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.MEMBERSHIP_SUSPENSION, sql_session)
            result = repo.restore(user_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"membership_restore_action error: {e}")
        return Err(str(e))
