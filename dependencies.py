from fastapi import Depends, HTTPException, status
from security import get_user_from_token
from db import get_user
from models import Users


def get_current_user(current_username: str = Depends(get_user_from_token)) -> dict:
    """
    Получает текущего пользователя по имени из токена.
    Возвращает словарь с данными пользователя.
    """
    user = get_user(current_username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user

def get_current_user_model(current_username: str = Depends(get_user_from_token)) -> Users:
    """
    Получает текущего пользователя как модель Users.
    """
    user = get_user(current_username)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return Users(**user)