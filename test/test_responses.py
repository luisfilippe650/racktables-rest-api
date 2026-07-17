from app.utils.responses import error_response


def test_error_response_always_includes_structured_detail():
    response = error_response("Object not found", status_code=404)

    assert response.status_code == 404
    body = response.body.decode()
    assert '"status":"error"' in body
    assert '"message":"Object not found"' in body
    assert '"reason":"not_found"' in body
    assert '"action":"Check the identifier and try again."' in body


def test_error_response_preserves_structured_detail_and_adds_defaults():
    response = error_response(
        "Invalid object type",
        status_code=400,
        detail={"context": "Object type ID: 1"},
    )

    body = response.body.decode()
    assert '"reason":"bad_request"' in body
    assert '"action":"Review the request data and try again."' in body
    assert '"context":"Object type ID: 1"' in body
