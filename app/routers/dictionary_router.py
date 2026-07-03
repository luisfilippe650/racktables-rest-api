from fastapi import APIRouter
from app.core.database import connect
from app.repository.objects.summary_repository import get_dictionary_options_for_chapter
from app.utils.responses import success_response, error_response

router = APIRouter(
    prefix="/dictionary",
    tags=["Dictionary"]
)

@router.get("/{chapter_id}")
def get_dictionary_options_route(chapter_id: int):
    database = connect()
    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)

    cursor = database.cursor(dictionary=True)
    try:
        options = get_dictionary_options_for_chapter(cursor, chapter_id)
        return success_response(data=options)
    except Exception as e:
        return error_response("An unexpected error occurred while fetching dictionary options", detail=str(e), status_code=500)
    finally:
        cursor.close()
        database.close()
