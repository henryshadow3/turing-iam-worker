import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def tenant_application_route_update_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        route_id = data.get("route_id")
        if not route_id:
            return Err("MISSING_FIELD_ROUTE_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.TENANT_APPLICATION_ROUTE, sql_session)
            result = repo.update(route_id, data)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"tenant_application_route_update_action error: {e}")
        return Err(str(e))
