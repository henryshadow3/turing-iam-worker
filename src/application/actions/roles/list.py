import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def role_list_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        tenant_id = data.get("tenant_id")
        repo = container.create_repository(RepositoryType.ROLE)
        result = repo.list_by_tenant(tenant_id)
        if isinstance(result, Ok):
            return Ok({"roles": result.ok_value})
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"role_list_action error: {e}")
        return Err(str(e))
