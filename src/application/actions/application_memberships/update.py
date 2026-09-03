import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def application_membership_update_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        application_membership_id = data.get("application_membership_id")
        role_id = data.get("role_id")
        if not application_membership_id or not role_id:
            return Err("MISSING_REQUIRED_FIELDS")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.APPLICATION_MEMBERSHIP, sql_session)
            result = repo.update(application_membership_id, role_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"application_membership_update_action error: {e}")
        return Err(str(e))
