from fastapi import HTTPException, status
from functools import wraps
from typing import List


class PermissionChecker:
    """
    Декоратор для проверки ролей пользователя.
    Использование: @PermissionChecker(["admin"])
    """
    def __init__(self, allowed_roles: List[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_user = kwargs.get("current_user")

            if not current_user:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Authentication required"
                )

            if isinstance(current_user, dict):
                user_roles = current_user.get("roles", [])
            else:
                user_roles = getattr(current_user, "roles", [])

            if "admin" in user_roles:
                return await func(*args, **kwargs)

            if not any(role in user_roles for role in self.allowed_roles):
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Insufficient permissions. Required roles: {self.allowed_roles}"
                )

            return await func(*args, **kwargs)

        return wrapper