import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def role_toggle_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        role_id = data.get("role_id")
        if not role_id:
            return Err("MISSING_FIELD_ROLE_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.ROLE, sql_session)
            result = repo.toggle(role_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"role_toggle_action error: {e}")
        return Err(str(e))
