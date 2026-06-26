import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def membership_delete_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        membership_id = data.get("membership_id")
        if not membership_id:
            return Err("MISSING_MEMBERSHIP_ID")
        repo = container.create_repository(RepositoryType.MEMBERSHIP)
        result = repo.delete(membership_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"membership_delete_action error: {e}")
        return Err(str(e))
