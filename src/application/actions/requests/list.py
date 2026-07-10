import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def request_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        # status opcional: por defecto solo las pendientes (la bandeja del admin).
        status = data.get("status", "pending")
        if status == "all":
            status = None
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.ACCESS_REQUEST, sql_session)
            result = repo.list_by_status(status)
        if isinstance(result, Ok):
            return Ok({"requests": result.ok_value})
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"request_list_action error: {e}")
        return Err(str(e))
