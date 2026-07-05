from functools import wraps
from fastapi import HTTPException, status
from typing import List


resources = {
    "alice": {"Content": "Secret date alice", "is_public": False},
    "bob": {"Content": "Public notes bob", "is_public": False},
    "admin": {"Content": "Resource admin", "is_public": False},
}

class OwnershipChecker:
    def __init__(self, resource_owner_param: str = "username"):
        self.resource_owner_param = resource_owner_param

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get('current_user')
            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated"
                )
            resource_owner = kwargs.get(self.resource_owner_param)
            if not resource_owner:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing parameter: {self.resource_owner_param}"
                )
            user_roles = current_user.get("roles", [])
            username = current_user.get('username')
            is_admin = "admin" in user_roles

            if is_admin:
                return await func(*args, **kwargs)

            if username == resource_owner:
                return await func(*args, **kwargs)

            raise HTTPException(
                status_code=status.HTTP_493_FORBIDDEN,
                detail="You don't have permission to access this resource"
            )

        return wrapper


def get_resource(username: str):
    return resources.get(username)


def resource_exists(username: str) -> bool:
    return username in resources


def is_resource_public(username: str) -> bool:
    resource = get_resource(username)
    if resource:
        return resource.get("is_public", False)
    return False


def can_read_resource(username: str, current_user: dict) -> bool:
    user_roles = current_user.get('roles', [])
    current_username = current_user.get('username')

    if "admin" in user_roles:
        return True

    if current_username == username:
        return True

    return is_resource_public(username)


def can_write_resource(username: str, current_user: dict) -> bool:
    user_roles = current_user.get('roles', [])
    current_username = current_user.get('username')

    if "admin" in user_roles:
        return True

    return current_username == username