import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def membership_update_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        membership_id = data.get("membership_id")
        role_id = data.get("role_id")
        if not membership_id or not role_id:
            return Err("MISSING_REQUIRED_FIELDS")
        repo = container.create_repository(RepositoryType.MEMBERSHIP)
        result = repo.update(membership_id, role_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"membership_update_action error: {e}")
        return Err(str(e))
