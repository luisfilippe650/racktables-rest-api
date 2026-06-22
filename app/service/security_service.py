import hashlib
from fastapi import HTTPException, status
from app.core.database import database_user
from app.core.security import create_access_token
from app.repository.security_repository import get_user
from app.utils.responses import error_response, success_response
from app.schema.security_schemas import UserModel


def authenticate_user(data: UserModel):
    database = database_user()
    if database is None:
        return None

    try:
        cursor = database.cursor(dictionary=True)
        # transformando em hash
        hash_password = hashlib.sha256(data.password.encode()).hexdigest()
        # buscando o usuario
        user = get_user(data.name, hash_password, cursor)

        if user is None:
            # raise instead of return so FastAPI will build the proper HTTP response
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")

        token = create_access_token(data={"user_id": user["id"]})

        return {
            "access_token": token
        }

    except Exception as error:
        # rollback and raise an HTTP error so client receives 503
        database.rollback()
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(error))

    finally:
        database.close()
        cursor.close()







