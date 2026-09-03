import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def user_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """iam.user.list.in — lista usuarios.

    Filtros y paginación OPCIONALES (aditivo, T-SP4-T2-I1-W7, requisito de
    Henry de que la búsqueda escale a miles de usuarios sin traer la tabla
    completa al cliente): search (texto libre sobre full_name/email), role
    (platform_role exacto), is_active (bool), limit/offset (paginación real).
    Ningún caller que no envíe estos campos ve cambio de comportamiento --
    solo se agrega "total" a la respuesta, que es aditivo.
    """
    try:
        search = data.get("search")
        role = data.get("role")
        is_active = data.get("is_active")
        limit = data.get("limit")
        offset = data.get("offset")

        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.USER, sql_session)
            result = repo.list_all(
                search=search,
                role=role,
                is_active=is_active,
                limit=limit,
                offset=offset,
            )
        if isinstance(result, Ok):
            payload = result.ok_value
            return Ok({"users": payload["users"], "total": payload["total"]})
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"user_list_action error: {e}")
        return Err(str(e))
