import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def member_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """Miembros del tenant ACTIVO del solicitante (admin del tenant).

    El tenant sale SIEMPRE de context["tenant_id"] (inyectado por turing-api
    desde el JWT), nunca del payload: un admin solo ve su propio tenant.
    Devuelve también los roles activos del tenant para el dropdown de cambio.
    """
    try:
        tenant_id = (context or {}).get("tenant_id")
        if not tenant_id:
            return Err("MISSING_ACTIVE_TENANT")

        with container.create_sql_session_manager() as sql_session:
            membership_repo = container.create_repository(RepositoryType.MEMBERSHIP, sql_session)
            role_repo       = container.create_repository(RepositoryType.ROLE, sql_session)
            members_res = membership_repo.list_by_tenant(tenant_id)
            roles_res   = role_repo.list_by_tenant(tenant_id)

        if not isinstance(members_res, Ok):
            return Err(members_res.err_value)
        if not isinstance(roles_res, Ok):
            return Err(roles_res.err_value)

        active_roles = [r for r in roles_res.ok_value if r["is_active"]]
        return Ok({"members": members_res.ok_value, "roles": active_roles})
    except Exception as e:
        logger.error(f"member_list_action error: {e}")
        return Err(str(e))
