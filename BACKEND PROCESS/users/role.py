def check_role(user_role, allowed_roles):

    if user_role in allowed_roles:
        return {
            "status": True,
            "message": "Access Granted"
        }

    return {
        "status": False,
        "message": "Access Denied"
    }