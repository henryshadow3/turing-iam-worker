import logging
from result import Ok

from application.events_manager import ACTIONS, DOMAIN_EVENTS

logger = logging.getLogger(__name__)


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
