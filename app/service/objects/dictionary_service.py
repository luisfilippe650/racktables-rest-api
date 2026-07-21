import logging

from app.core.database import connect_with_cursor
from app.repository.objects.summary_repository import (
    count_dictionary_options_for_chapter,
    dictionary_chapter_exists,
    get_dictionary_options_for_chapter,
)
from app.utils.responses import error_response, paginated_response
from app.utils.database_resources import close_database_resources

logger = logging.getLogger(__name__)

def get_dictionary(chapter_id: int, page: int = 1, per_page: int = 50):
    if chapter_id <= 0:
        return error_response("Chapter ID must be greater than zero", status_code=400)
    if page < 1:
        return error_response("Page must be greater than or equal to 1", status_code=400)
    if per_page < 1 or per_page > 100:
        return error_response("Per page must be between 1 and 100", status_code=400)

    database, cursor = connect_with_cursor()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)

    try:
        if not dictionary_chapter_exists(cursor, chapter_id):
            return error_response(f"Dictionary chapter {chapter_id} not found", status_code=404)

        offset = (page - 1) * per_page
        total = count_dictionary_options_for_chapter(cursor, chapter_id)
        options = get_dictionary_options_for_chapter(cursor, chapter_id, per_page, offset)

        return paginated_response(options, page, per_page, total)

    except Exception as e:
        logger.exception("Unexpected error while fetching dictionary options")
        return error_response("An unexpected error occurred while fetching dictionary options", status_code=500)
    finally:
        close_database_resources(database, cursor, logger)
