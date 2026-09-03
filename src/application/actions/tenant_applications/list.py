import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def tenant_application_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        tenant_id = data.get("tenant_id")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.TENANT_APPLICATION, sql_session)
            result = repo.list_all(tenant_id)
        if isinstance(result, Ok):
            return Ok({"tenant_applications": result.ok_value})
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"tenant_application_list_action error: {e}")
        return Err(str(e))
