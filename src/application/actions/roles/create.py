import logging
from typing import Dict, Any
from result import Result, Ok, Err

from infrastructure.di.container import RepositoryType

logger = logging.getLogger(__name__)


def role_create_action(data: Dict[str, Any], context: Dict[str, Any], container) -> Result[Any, str]:
    """iam.role.create.in — crea un rol en el modelo híbrido de turing.roles
    (ADR 0001 §4/§5, migración 017 de db-turing). Tres combinaciones válidas
    (mismo CHECK que roles_scope_chk en BD, validadas aquí primero para dar
    un Err(...) legible en vez de depender de la excepción cruda del CHECK):

      - Catálogo por aplicación: tenant_id NULL, application_id presente.
      - Custom por tenant-aplicación: tenant_id presente, application_id presente.
      - Legacy organizacional (comportamiento actual, intacto): tenant_id
        presente, application_id NULL.

    `name` siempre es requerido. `application_id` es opcional -- si no viene,
    se asume legacy y tenant_id pasa a ser obligatorio (mismo comportamiento
    que antes de este Work Item, sin romper consumidores existentes).
    """
    try:
        if not data.get("name"):
            return Err("MISSING_FIELD_NAME")

        tenant_id = data.get("tenant_id")
        application_id = data.get("application_id")

        # (tenant_id IS NULL, application_id IS NULL) es el único caso sin
        # combinación válida en roles_scope_chk -- todas las demás
        # combinaciones de presencia/ausencia son válidas (catálogo, custom,
        # legacy). MISSING_FIELD_TENANT_ID conserva el mensaje legacy para no
        # romper consumidores que ya lo esperaban cuando no se envía ningún
        # scope.
        if not tenant_id and not application_id:
            return Err("MISSING_FIELD_TENANT_ID")

        with container.create_sql_session_manager() as sql_session:
            repo = container.create_repository(RepositoryType.ROLE, sql_session)
            result = repo.create(data)
        if isinstance(result, Ok):
            return Ok(result.ok_value)
        return Err(result.err_value)
    except Exception as e:
        logger.error(f"role_create_action error: {e}")
        return Err(str(e))
