from app.repository.objects.objects_repository import (
    count_all_objects_query,
    list_all_objects_query,
)


class FakeCursor:
    def __init__(self, fetchone_result=None, fetchall_result=None):
        self.executed = []
        self.fetchone_result = fetchone_result or {"count": 0}
        self.fetchall_result = fetchall_result or []

    def execute(self, query, params=None):
        self.executed.append((query, params or ()))

    def fetchone(self):
        return self.fetchone_result

    def fetchall(self):
        return self.fetchall_result


def test_count_all_objects_without_search_does_not_join_dictionary():
    cursor = FakeCursor({"count": 10})

    result = count_all_objects_query(cursor)

    query, params = cursor.executed[0]
    assert result == 10
    assert "FROM Object" in query
    assert "JOIN Dictionary" not in query
    assert params == ()


def test_list_all_objects_search_escapes_like_wildcards():
    cursor = FakeCursor(fetchall_result=[])

    list_all_objects_query(cursor, limit=15, offset=0, search=r"POLON_%\\")

    query, params = cursor.executed[0]
    assert "ESCAPE" in query
    assert params[:-2] == (r"%POLON\_\%\\\\%",) * 8
    assert params[-2:] == (15, 0)
