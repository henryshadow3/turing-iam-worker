import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def role_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """iam.role.list.in — lista roles del modelo híbrido (ADR 0001 §5).

    Acepta `tenant_id` (comportamiento legacy: roles de ese tenant, incluye
    también sus roles custom por aplicación) y/o `application_id` (nuevo:
    roles de catálogo o custom de esa aplicación) como filtros
    independientes y combinables. Sin filtros, devuelve todos los roles --
    la UI (ApplicationAccesses.jsx) usa `application_id` para resolver el
    combo de roles disponibles al elegir una aplicación, incluyendo tanto el
    catálogo compartido como los custom del tenant activo.
    """
    try:
        tenant_id = data.get("tenant_id")
        application_id = data.get("application_id")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.ROLE, sql_session)
            result = repo.list_by_tenant(tenant_id, application_id)
        if isinstance(result, Ok):
            return Ok({"roles": result.ok_value})
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"role_list_action error: {e}")
        return Err(str(e))
