import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def tenant_create_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    try:
        for field in ["slug", "name", "redirect_url"]:
            if not data.get(field):
                return Err(f"MISSING_FIELD_{field.upper()}")
        repo = container.create_repository(RepositoryType.TENANT)
        result = repo.create(data)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"tenant_create_action error: {e}")
        return Err(str(e))
