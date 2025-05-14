from datetime import timedelta

from flask_jwt_extended import create_access_token


def verify_token_error_response(response, expected_code, status_code=401):
    assert response.status_code == status_code
    data = response.get_json()
    assert "error" in data
    assert data["code"] == expected_code


def get_auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def get_expired_token_headers(app_context, id=1):
    with app_context:
        token = create_access_token(
            identity=str(id), expires_delta=timedelta(seconds=-1)
        )
        return get_auth_header(token)


def get_invalid_token_headers():
    return get_auth_header("invalid.token.format")
