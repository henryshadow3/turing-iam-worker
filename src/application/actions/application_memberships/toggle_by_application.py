import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def application_membership_toggle_by_application_action(
    data: Dict[str, Any], context: Dict[str, Any], container
) -> Result[Any, str]:
    """iam.user.toggle_application_access.in — alterna, en una sola
    transacción, TODOS los application_memberships de un usuario para una
    aplicación (cruzando todos los tenants donde tiene acceso a esa app),
    T-SP4-T2-I1-W12. Ver ApplicationMembershipPostgresRepository.
    toggle_by_application para la semántica exacta y su justificación.
    """
    try:
        user_id = data.get("user_id")
        application_id = data.get("application_id")
        if not user_id:
            return Err("MISSING_FIELD_USER_ID")
        if not application_id:
            return Err("MISSING_FIELD_APPLICATION_ID")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.APPLICATION_MEMBERSHIP, sql_session)
            result = repo.toggle_by_application(user_id, application_id)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"application_membership_toggle_by_application_action error: {e}")
        return Err(str(e))
