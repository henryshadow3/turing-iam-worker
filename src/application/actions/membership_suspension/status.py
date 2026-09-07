import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def membership_suspension_status_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """iam.user.membership_suspension_status.in — {"suspended": true/false}
    según si existe una suspensión global vigente (W11, T-SP4-T2-I1). Usado
    por UserDetailPanel al abrir el panel para decidir si mostrar
    "Suspender membresía" o "Restaurar membresía".
    """
    try:
        user_id = data.get("user_id")
        if not user_id:
            return Err("MISSING_FIELD_USER_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.MEMBERSHIP_SUSPENSION, sql_session)
            result = repo.status(user_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"membership_suspension_status_action error: {e}")
        return Err(str(e))
