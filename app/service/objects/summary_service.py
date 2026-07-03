from app.core.database import connect
from app.repository.objects.summary_repository import get_object_attributes
from app.utils.responses import success_response, error_response

def get_object_summary_service(object_id: int):
    database = connect()

    if not database:
        return error_response("Internal server error: failed to connect to the database", status_code=500)
    
    cursor = database.cursor(dictionary=True)

    try:
        result = get_object_attributes(cursor, object_id)

        if result is None:
            return error_response("Object not found", status_code=404)

        return success_response(data=result)

    except Exception as e:
        return error_response("An unexpected error occurred", detail=str(e), status_code=500)

    finally:
        if database.is_connected():
            cursor.close()
            database.close()
