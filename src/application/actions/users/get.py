import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def user_get_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        user_id = data.get("user_id")
        if not user_id:
            return Err("MISSING_USER_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.USER, sql_session)
            result = repo.get_by_id(user_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"user_get_action error: {e}")
        return Err(str(e))
