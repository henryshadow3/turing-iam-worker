import logging
from result import Ok

from application.events_manager import ACTIONS, DOMAIN_EVENTS

logger = logging.getLogger(__name__)

# Rol de plataforma que puede operar el IAM.
PLATFORM_SUPERADMIN = "superadmin"

# Verbos de escritura que MODIFICAN el estado IAM. Solo el superadmin de
# plataforma puede ejecutarlos. Las lecturas (list/get) quedan abiertas a
# cualquier usuario autenticado. El evento tiene forma "iam.<recurso>.<verbo>.in".
IAM_WRITE_VERBS = {"create", "update", "delete", "disable", "toggle", "approve", "reject"}


def _requires_superadmin(event: str) -> bool:
    parts = event.split(".")
    # ["iam", "<recurso>", "<verbo>", "in"]
    return len(parts) >= 3 and parts[0] == "iam" and parts[2] in IAM_WRITE_VERBS


def business_logic(data: dict, context: dict, container) -> dict:
    try:
        event = context.get("event")
        if not event:
            logger.error("Event missing from context")
            return _error_response("EVENT_MISSING")

        logger.info(f"Processing event: {event}")

        action = ACTIONS.get(event)
        if not action:
            logger.error(f"No action registered for event: {event}")
            return _error_response("EVENT_NOT_FOUND")

        # Autorización de plataforma: las escrituras IAM exigen superadmin.
        # Ser admin de un tenant NO da acceso a operar el IAM.
        if _requires_superadmin(event):
            platform_role = (context or {}).get("platform_role") or ""
            if platform_role != PLATFORM_SUPERADMIN:
                logger.warning(
                    f"Forbidden IAM write {event}: platform_role='{platform_role}'"
                )
                return _error_response("FORBIDDEN_REQUIRES_SUPERADMIN")

        result = action(data, context, container)

        if isinstance(result, Ok):
            return {
                "response":      result.ok_value,
                "domain_events": DOMAIN_EVENTS.get(event, []),
                "error":         None,
            }

        logger.error(f"Action returned error for {event}: {result.err_value}")
        return _error_response(str(result.err_value))

    except Exception as e:
        logger.error(f"Unexpected error in business_logic: {e}", exc_info=True)
        return _error_response("INTERNAL_ERROR")


def _error_response(error_code: str) -> dict:
    return {"response": None, "domain_events": [], "error": error_code}
