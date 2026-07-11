import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def member_toggle_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """Activa/desactiva una membresía del tenant activo (admin del tenant).

    Valida que la membresía pertenezca al tenant del context y que el admin
    no se desactive a sí mismo.
    """
    try:
        tenant_id = (context or {}).get("tenant_id")
        actor_id  = (context or {}).get("user_id")
        if not tenant_id:
            return Err("MISSING_ACTIVE_TENANT")
        membership_id = data.get("membership_id")
        if not membership_id:
            return Err("MISSING_FIELD_MEMBERSHIP_ID")

        with container.create_sql_session_manager() as sql_session:
            membership_repo = container.create_repository(RepositoryType.MEMBERSHIP, sql_session)

            current = membership_repo.get_by_id(membership_id)
            if not isinstance(current, Ok):
                return Err(current.err_value)
            membership = current.ok_value
            if membership["tenant_id"] != tenant_id:
                return Err("FORBIDDEN_OTHER_TENANT")
            if actor_id and membership["user_id"] == actor_id:
                return Err("CANNOT_MODIFY_OWN_MEMBERSHIP")

            result = membership_repo.toggle(membership_id)

        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"member_toggle_action error: {e}")
        return Err(str(e))
