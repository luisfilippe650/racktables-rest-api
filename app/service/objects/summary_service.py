import logging

from app.core.database import connect_with_cursor
from app.repository.objects.summary_repository import get_object_attributes
from app.utils.responses import success_response, error_response
from app.utils.database_resources import close_database_resources

logger = logging.getLogger(__name__)

def get_object_summary_service(object_id: int, include_options: bool = False):
    database, cursor = connect_with_cursor()

    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)

    try:
        cursor.execute("SET SESSION time_zone = '+00:00'")
        result = get_object_attributes(cursor, object_id, include_options=include_options)

        if result is None:
            return error_response("Object not found", status_code=404)

        return success_response(data=result)

    except Exception as e:
        logger.exception("Unexpected error while getting object summary")
        return error_response("An unexpected error occurred while getting object summary", status_code=500)

    finally:
        close_database_resources(database, cursor, logger)
