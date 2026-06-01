import os
from pathlib import Path
from datetime import timedelta
import environ
 
BASE_DIR = Path(__file__).resolve().parent.parent
 
env = environ.Env()
environ.Env.read_env(BASE_DIR / ".env")
 
# SECURITY
SECRET_KEY = env("SECRET_KEY")
DEBUG = env.bool("DEBUG", default=False)
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=[])
 
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "django_filters",
    "corsheaders",
    "app.users",
    "app.webhooks",
    "app.events",
    "app.deliveries",
]
 
AUTH_USER_MODEL = "users.User"
 
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
]
 
# Lock this down to specific origins before deploying.
# CORS_ALLOW_ALL_ORIGINS = True is acceptable for local dev only.
CORS_ALLOW_ALL_ORIGINS = env.bool("CORS_ALLOW_ALL_ORIGINS", default=False)
CORS_ALLOWED_ORIGINS = env.list("CORS_ALLOWED_ORIGINS", default=[])
 
ROOT_URLCONF = "core.urls"
 
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]
 
WSGI_APPLICATION = "core.wsgi.application"
 
DATABASES = {
    "default": env.db("DATABASE_URL")
}
 
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
}
 
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=1),
    "AUTH_HEADER_TYPES": ("Bearer",),
}
 
# CELERY
CELERY_BROKER_URL = env("REDIS_URL")
 
# Without a result backend, you cannot inspect task state (success/failure/retry).
# This was missing in the original — Celery would run silently with no observable state.
CELERY_RESULT_BACKEND = env("REDIS_URL")
 
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
 
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
 
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
