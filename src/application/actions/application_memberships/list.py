import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def application_membership_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        user_id = data.get("user_id")
        tenant_application_id = data.get("tenant_application_id")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.APPLICATION_MEMBERSHIP, sql_session)
            result = repo.list_all(user_id=user_id, tenant_application_id=tenant_application_id)
        if isinstance(result, Ok):
            return Ok({"application_memberships": result.ok_value})
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"application_membership_list_action error: {e}")
        return Err(str(e))
