import sentry_sdk
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.asyncio import AsyncioIntegration
from config import settings


def init_glitchtip():
    """Инициализация GlitchTip через Sentry SDK"""

    if not settings.GLITCHTIP_DSN:
        print("GLITCHTIP_DSN не задан. Отслеживание ошибок отключено.")
        return

    print(f"Инициализация GlitchTip (env: {settings.APP_ENV})")

    sentry_sdk.init(
        dsn=settings.GLITCHTIP_DSN,
        environment=settings.APP_ENV,
        release="1.0.0",
        integrations=[
            FastApiIntegration(),
            AsyncioIntegration(),
        ],
        traces_sample_rate=1.0,
    )

    print("GlitchTip инициализирован")