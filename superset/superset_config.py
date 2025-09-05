import os
from typing import Optional

# Database configuration
SQLALCHEMY_DATABASE_URI = (
    f"postgresql+psycopg2://"
    f"{os.environ.get('DATABASE_USER', 'superset')}:"
    f"{os.environ.get('DATABASE_PASSWORD', 'superset_password')}@"
    f"{os.environ.get('DATABASE_HOST', 'db')}:"
    f"{os.environ.get('DATABASE_PORT', '5432')}/"
    f"{os.environ.get('DATABASE_DB', 'superset')}"
)

# Redis configuration for caching
REDIS_HOST = os.environ.get('REDIS_HOST', 'cache')
REDIS_PORT = int(os.environ.get('REDIS_PORT', 6379))
REDIS_DB = int(os.environ.get('REDIS_DB', 1))

# Cache configuration
CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 300,
    'CACHE_KEY_PREFIX': 'superset_',
    'CACHE_REDIS_HOST': REDIS_HOST,
    'CACHE_REDIS_PORT': REDIS_PORT,
    'CACHE_REDIS_DB': REDIS_DB,
}

# Results cache
RESULTS_BACKEND = {
    'cache_type': 'RedisCache',
    'cache_default_timeout': 86400,  # 1 day
    'cache_key_prefix': 'superset_results_',
    'cache_redis_host': REDIS_HOST,
    'cache_redis_port': REDIS_PORT,
    'cache_redis_db': REDIS_DB + 1,
}

# Secret key for sessions
SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'superset_secret_key_change_me')

# Feature flags
FEATURE_FLAGS = {
    'DASHBOARD_NATIVE_FILTERS': True,
    'DASHBOARD_CROSS_FILTERS': True,
    'DASHBOARD_FILTERS_EXPERIMENTAL': True,
    'EMBEDDABLE_CHARTS': True,
    'ESCAPE_MARKDOWN_HTML': True,
    'ENABLE_TEMPLATE_PROCESSING': True,
    'LISTVIEWS_DEFAULT_CARD_VIEW': True,
    'SQLLAB_BACKEND_PERSISTENCE': True,
    'THUMBNAILS': True,
    'ALERT_REPORTS': True,
}

# Security configuration
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# SQL Lab configuration
SQLLAB_CTAS_NO_LIMIT = True
SQLLAB_QUERY_COST_ESTIMATE_ENABLED = False
SQLLAB_TIMEOUT = 300  # 5 minutes
SUPERSET_WEBSERVER_TIMEOUT = 300

# Email configuration (optional)
EMAIL_NOTIFICATIONS = False
SMTP_HOST = os.environ.get('SMTP_HOST', 'localhost')
SMTP_STARTTLS = True
SMTP_SSL = False
SMTP_USER = os.environ.get('SMTP_USER', '')
SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD', '')
SMTP_MAIL_FROM = os.environ.get('SMTP_MAIL_FROM', 'superset@eduanalytics.local')

# Logging configuration
ENABLE_TIME_ROTATE = True
TIME_ROTATE_LOG_LEVEL = 'INFO'
FILENAME = os.path.join('/app/superset_home', 'superset.log')

# Dashboard and chart configuration
DASHBOARD_AUTO_REFRESH_INTERVALS = [
    [0, "Don't refresh"],
    [10, "10 seconds"],
    [30, "30 seconds"],
    [60, "1 minute"],
    [300, "5 minutes"],
    [1800, "30 minutes"],
    [3600, "1 hour"],
]

# Custom CSS (optional)
# APP_ICON = "/static/assets/images/superset-logo-horiz.png"
# FAVICONS = [{"href": "/static/assets/images/favicon.png"}]

# Row limit for SQL Lab
DEFAULT_SQLLAB_LIMIT = 5000
SQL_MAX_ROW = 100000

# Enable public role for embedding
PUBLIC_ROLE_LIKE = 'Gamma'
ENABLE_PROXY_FIX = True

# Language support
LANGUAGES = {
    'en': {'flag': 'us', 'name': 'English'},
    'ru': {'flag': 'ru', 'name': 'Russian'},
}

# Database connections for EduAnalytics
EDUANALYTICS_DB_URI = (
    f"postgresql+psycopg2://"
    f"superset:"
    f"superset_password@"
    f"db:5432/eduanalytics"
)

# Custom database connections can be added through the UI
# This config provides defaults for connecting to EduAnalytics data
