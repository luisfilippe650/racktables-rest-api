from fastapi import APIRouter, Path, Query
from app.service.objects.dictionary_service import get_dictionary

router = APIRouter(
    prefix="/dictionary",
    tags=["Dictionary"]
)

@router.get("/{chapter_id}")
def get_dictionary_options_router(
    chapter_id: int = Path(..., ge=1),
    page: int = Query(1, ge=1, le=1000),
    per_page: int = Query(50, ge=1, le=100)
):
    return get_dictionary(chapter_id, page, per_page)
