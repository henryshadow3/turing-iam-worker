import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def tenant_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        repo = container.create_repository(RepositoryType.TENANT)
        result = repo.list_all()
        if isinstance(result, Ok):
            return Ok({"tenants": result.ok_value})
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"tenant_list_action error: {e}")
        return Err(str(e))
