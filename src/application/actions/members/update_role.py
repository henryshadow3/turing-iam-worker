import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def member_update_role_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """Cambia el rol de una membresía del tenant activo (admin del tenant).

    Valida que la membresía pertenezca al tenant del context, que el rol nuevo
    sea de ese tenant y esté activo, y que el admin no se modifique a sí mismo.
    """
    try:
        tenant_id = (context or {}).get("tenant_id")
        actor_id  = (context or {}).get("user_id")
        if not tenant_id:
            return Err("MISSING_ACTIVE_TENANT")
        membership_id = data.get("membership_id")
        role_id       = data.get("role_id")
        if not membership_id or not role_id:
            return Err("MISSING_REQUIRED_FIELDS")

        with container.create_sql_session_manager() as sql_session:
            membership_repo = container.create_repository(RepositoryType.MEMBERSHIP, sql_session)
            role_repo       = container.create_repository(RepositoryType.ROLE, sql_session)

            current = membership_repo.get_by_id(membership_id)
            if not isinstance(current, Ok):
                return Err(current.err_value)
            membership = current.ok_value
            if membership["tenant_id"] != tenant_id:
                return Err("FORBIDDEN_OTHER_TENANT")
            if actor_id and membership["user_id"] == actor_id:
                return Err("CANNOT_MODIFY_OWN_MEMBERSHIP")

            role_res = role_repo.get_by_id(role_id)
            if not isinstance(role_res, Ok):
                return Err(role_res.err_value)
            role = role_res.ok_value
            if role["tenant_id"] != tenant_id:
                return Err("ROLE_TENANT_MISMATCH")
            if not role["is_active"]:
                return Err("ROLE_INACTIVE")

            result = membership_repo.update(membership_id, role_id)

        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"member_update_role_action error: {e}")
        return Err(str(e))
