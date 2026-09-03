import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def application_membership_toggle_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        application_membership_id = data.get("application_membership_id")
        if not application_membership_id:
            return Err("MISSING_FIELD_APPLICATION_MEMBERSHIP_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.APPLICATION_MEMBERSHIP, sql_session)
            result = repo.toggle(application_membership_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"application_membership_toggle_action error: {e}")
        return Err(str(e))
