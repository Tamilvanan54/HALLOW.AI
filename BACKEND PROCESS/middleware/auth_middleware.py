from auth.jwt import verify_access_token


def authenticate_user(token):

    payload = verify_access_token(token)

    if payload is None:
        return {
            "status": False,
            "message": "Unauthorized"
        }

    return {
        "status": True,
        "user": payload
    }