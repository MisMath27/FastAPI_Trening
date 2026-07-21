# core/logger.py
import sys
import json
from datetime import datetime
from typing import Any, Dict, Optional
from fastapi import Request
from loguru import logger
import re

# Конфигурация Loguru
logger.remove()  # Удаляем стандартный обработчик

# Формат для вывода в консоль
logger.add(
    sys.stdout,
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
    level="DEBUG",
    colorize=True,
    serialize=False,  # Для читаемого вывода в консоль
    backtrace=True,
    diagnose=True,
)

# Формат для вывода в JSON (структурированный лог)
logger.add(
    "logs/app_{time:YYYY-MM-DD}.json",
    format="{message}",
    level="INFO",
    serialize=True,  # JSON формат
    rotation="1 day",
    retention="30 days",
    compression="zip",
)

# Список чувствительных заголовков для маскирования
SENSITIVE_HEADERS = {
    "authorization", "cookie", "set-cookie", "x-api-key",
    "x-api-secret", "api-key", "api-secret", "token",
    "access-token", "refresh-token", "password", "secret"
}

SENSITIVE_FIELDS = {
    "password", "token", "access_token", "refresh_token",
    "secret", "api_key", "api_secret", "credit_card",
    "card_number", "cvv", "ssn", "passport"
}

MAX_BODY_SIZE = 2048  # Максимальный размер логируемого тела


def mask_sensitive_data(data: Any, depth: int = 0) -> Any:
    """Маскирует чувствительные данные в словарях и строках"""
    if depth > 10:
        return data

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            key_lower = key.lower()
            if any(sensitive in key_lower for sensitive in SENSITIVE_FIELDS):
                result[key] = "***MASKED***"
            else:
                result[key] = mask_sensitive_data(value, depth + 1)
        return result
    elif isinstance(data, list):
        return [mask_sensitive_data(item, depth + 1) for item in data]
    elif isinstance(data, str):
        # Простые паттерны для маскировки
        patterns = [
            (r'(token["\s:=]+)[a-zA-Z0-9\-_\.]+', r'\1***MASKED***'),
            (r'(password["\s:=]+)[^\s,}]+', r'\1***MASKED***'),
            (r'(api[_-]?key["\s:=]+)[a-zA-Z0-9\-_]+', r'\1***MASKED***'),
        ]
        result = data
        for pattern, replacement in patterns:
            result = re.sub(pattern, replacement, result, flags=re.IGNORECASE)
        return result
    else:
        return data


def safe_get_body(request: Request) -> Optional[str]:
    """Безопасное извлечение тела запроса"""
    try:
        import asyncio
        if not hasattr(request, "_body"):
            return None

        body = request._body
        if isinstance(body, bytes):
            body = body.decode("utf-8", errors="ignore")
        if isinstance(body, str):
            if len(body) > MAX_BODY_SIZE:
                body = body[:MAX_BODY_SIZE] + f"... [TRUNCATED, {len(body)} bytes total]"
            return body
        return str(body)[:MAX_BODY_SIZE]
    except Exception:
        return "[ERROR READING BODY]"


def extract_request_context(request: Request) -> Dict[str, Any]:
    """Извлекает полный контекст запроса"""
    context = {
        "method": request.method,
        "path": request.url.path,
        "client_host": request.client.host if request.client else None,
        "client_port": request.client.port if request.client else None,
        "query_params": dict(request.query_params) if request.query_params else {},
        "path_params": getattr(request, "path_params", {}),
        "headers": {},
        "cookies": {},
        "body": None,
        "content_type": request.headers.get("content-type"),
    }

    # Заголовки (маскируем чувствительные)
    for key, value in request.headers.items():
        key_lower = key.lower()
        if key_lower in SENSITIVE_HEADERS:
            context["headers"][key] = "***MASKED***"
        else:
            context["headers"][key] = value

    # Cookies (маскируем полностью)
    if request.cookies:
        context["cookies"] = {k: "***MASKED***" for k in request.cookies.keys()}

    # Тело запроса (безопасно)
    context["body"] = safe_get_body(request)

    # Для multipart/form-data - только метаданные
    content_type = context["content_type"] or ""
    if "multipart/form-data" in content_type:
        context["body"] = "[MULTIPART FORM DATA - content not logged]"
        # Можно добавить информацию о файлах
        if hasattr(request, "_form"):
            try:
                files_info = []
                for key, value in request._form.items():
                    if hasattr(value, "filename"):
                        files_info.append({
                            "field": key,
                            "filename": value.filename,
                            "size": getattr(value, "size", None)
                        })
                if files_info:
                    context["files"] = files_info
            except Exception:
                pass

    return context


def log_error(
    request: Request,
    exc: Exception,
    *,
    status_code: int = 500,
    request_id: Optional[str] = None,
    extra_context: Optional[Dict] = None,
) -> None:
    """Основная функция для логирования ошибок с полным контекстом"""
    try:
        # Извлекаем контекст запроса
        context = extract_request_context(request)

        # Добавляем request_id
        if request_id:
            context["request_id"] = request_id
        else:
            # Пытаемся получить из заголовка X-Request-ID
            request_id = request.headers.get("x-request-id")
            if request_id:
                context["request_id"] = request_id

        # Добавляем статус код
        context["status_code"] = status_code

        # Добавляем информацию об ошибке
        context["error_type"] = type(exc).__name__
        context["error_message"] = str(exc)

        # Добавляем traceback (включая полный стек)
        import traceback
        context["traceback"] = traceback.format_exc()

        # Добавляем дополнительный контекст
        if extra_context:
            context.update(extra_context)

        # Маскируем чувствительные данные
        context = mask_sensitive_data(context)

        # Логируем с bind (все поля будут в JSON)
        bound_logger = logger.bind(**context)
        bound_logger.opt(exception=exc).error(f"Request failed: {status_code}")

    except Exception as log_error:
        # Фолбэк - если что-то пошло не так при логировании
        try:
            logger.error(f"!!! LOGGER ERROR: {log_error}")
            logger.error(f"Original exception: {exc}")
        except Exception:
            # Абсолютный фолбэк - просто печатаем в консоль
            print(f"CRITICAL: Failed to log error: {exc}")


def log_success(request: Request, status_code: int = 200, extra_context: Optional[Dict] = None) -> None:
    """Логирование успешных запросов (опционально)"""
    try:
        context = extract_request_context(request)
        context["status_code"] = status_code

        if extra_context:
            context.update(extra_context)

        context = mask_sensitive_data(context)
        bound_logger = logger.bind(**context)
        bound_logger.info(f"Request completed: {status_code}")
    except Exception:
        pass