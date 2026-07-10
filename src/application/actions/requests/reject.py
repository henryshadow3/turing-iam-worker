import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def request_reject_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        request_id = data.get("request_id")
        if not request_id:
            return Err("MISSING_FIELD_REQUEST_ID")
        note = data.get("note")
        resolved_by = (context or {}).get("user_id")

        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.ACCESS_REQUEST, sql_session)
            result = repo.reject(request_id, resolved_by, note)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"request_reject_action error: {e}")
        return Err(str(e))
