import logging

from app.core.database import connect
from app.repository.objects.summary_repository import (
    count_dictionary_options_for_chapter,
    dictionary_chapter_exists,
    get_dictionary_options_for_chapter,
)
from app.utils.responses import success_response, error_response

logger = logging.getLogger(__name__)

def get_dictionary(chapter_id: int, page: int = 1, per_page: int = 50):
    if chapter_id <= 0:
        return error_response("Chapter ID must be greater than zero", status_code=400)
    if page < 1:
        return error_response("Page must be greater than or equal to 1", status_code=400)
    if per_page < 1 or per_page > 100:
        return error_response("Per page must be between 1 and 100", status_code=400)

    database = connect()

    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)

    cursor = database.cursor(dictionary=True)

    try:
        if not dictionary_chapter_exists(cursor, chapter_id):
            return error_response(f"Dictionary chapter {chapter_id} not found", status_code=404)

        offset = (page - 1) * per_page
        total = count_dictionary_options_for_chapter(cursor, chapter_id)
        options = get_dictionary_options_for_chapter(cursor, chapter_id, per_page, offset)

        return success_response(
            data={
                "items": options,
                "page": page,
                "per_page": per_page,
                "total": total
            },
            count=len(options)
        )

    except Exception as e:
        logger.exception("Unexpected error while fetching dictionary options")
        return error_response("An unexpected error occurred while fetching dictionary options", status_code=500)
    finally:
        cursor.close()
        database.close()
