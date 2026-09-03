import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def application_membership_create_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """iam.application_membership.create.in — otorga acceso REAL a una
    tenant-aplicación (ADR 0001). Distinto de iam.membership.create.in (que
    solo crea afiliación al tenant, ver [[iam-worker-proto-passthrough-pattern]]
    y el ADR §1). Exige user_id + tenant_application_id + role_id explícitos
    y valida afiliación activa previa antes de escribir (regla dura del
    Work Item W5) -- la validación fuerte vive en el repositorio
    (ApplicationMembershipPostgresRepository.create) para mantener las
    reglas de negocio junto a las demás validaciones cruzadas (rol
    perteneciente a la app, tenant_application activa, etc.) en un solo
    lugar; esta action solo valida presencia de campos, igual que el resto
    de actions *_create de este worker.
    """
    try:
        for field in ["user_id", "tenant_application_id", "role_id"]:
            if not data.get(field):
                return Err(f"MISSING_FIELD_{field.upper()}")
        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.APPLICATION_MEMBERSHIP, sql_session)
            result = repo.create(data)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"application_membership_create_action error: {e}")
        return Err(str(e))
