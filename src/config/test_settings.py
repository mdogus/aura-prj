"""
Test ortamı ayarları.
Güvenlik middleware'lerini (HTTPS yönlendirmesi vb.) devre dışı bırakır;
testler HTTP üzerinden çalışır.
"""
from config.settings import *  # noqa: F401, F403

DEBUG = True
SECURE_SSL_REDIRECT = False
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
