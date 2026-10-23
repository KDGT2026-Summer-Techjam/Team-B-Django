"""
Django settings for config project.
"""

import os
import sys
from pathlib import Path

import dj_database_url
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ["SECRET_KEY"]

DEBUG = os.environ.get("DEBUG", "False") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

# `python manage.py test` で実行しているか（下の STORAGES と同じ判定）
TESTING = "test" in sys.argv

# 本番（DEBUG=False）のときだけ有効にするHTTPS・Cookieのセキュリティ設定。
# ローカル開発（DEBUG=True、http://localhost）と、テスト（http://testserver）には影響しない。
# `python manage.py check --deploy` の警告（W004 / W008 / W016）への対応。
# HTTPSの判定に使う SECURE_PROXY_SSL_HEADER は、下の「Render のリバースプロキシ」の項で設定している。
if not DEBUG and not TESTING:
    # HTTPでのアクセスを、HTTPSへリダイレクトする。
    SECURE_SSL_REDIRECT = True
    # ログイン状態（セッション）とCSRFトークンのCookieを、HTTPS経由でのみ送る。
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # ブラウザに「このサイトは一定期間HTTPSでのみ接続する」と覚えさせる（HSTS）。
    # 一度設定すると、期間内はブラウザがHTTPで接続できなくなるため、まず1時間から始め、
    # 問題がないことを確認してから段階的に延ばす（最終的には1年 = 31536000 を目安にする）。
    SECURE_HSTS_SECONDS = 3600
    # このサイト（seasonhub-web.onrender.com）にサブドメインはなく、すべてHTTPSで配信されるため問題ない（W005）。
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    # W021（HSTSプリロードリストへの登録）は、自分で所有するドメインだけが対象。
    # *.onrender.com は登録できないため、意図的に無効にする。独自ドメインを使うようになったら見直す。
    SILENCED_SYSTEM_CHECKS = ["security.W021"]


# Application definition

INSTALLED_APPS = [
    "django.contrib.staticfiles",
    "events",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "events.middleware.VisitorIdMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# Database
# docs/設計.md 参照。本番（Render）は DATABASE_URL で PostgreSQL に接続する
# ローカル開発は DATABASE_URL 未設定なら SQLite にフォールバックする

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}


# Internationalization

LANGUAGE_CODE = "ja"

TIME_ZONE = "Asia/Tokyo"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# docs/deploy.md 参照。静的ファイルはバックエンド（WhiteNoise）から配信する

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
# テスト実行時はDjangoがDEBUGを強制的にFalseにするため、
# collectstatic未実行の環境ではCompressedManifestStaticFilesStorageが
# manifestを参照できずエラーになる。テスト時だけmanifest不要のstorageに切り替える
STORAGES = {
    "staticfiles": {
        "BACKEND": (
            "django.contrib.staticfiles.storage.StaticFilesStorage"
            if "test" in sys.argv
            else "whitenoise.storage.CompressedManifestStaticFilesStorage"
        ),
    },
}

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# ミッション写真(Base64)を含むリクエストを受け取るための上限。
# Djangoの既定は2.5MBで、超えるとビューに到達する前に400になる。
# 写真の上限14MBに対し、JSONのキーやdata URLの接頭辞の分だけ余裕を持たせる
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024

# Render のリバースプロキシ経由の HTTPS 判定
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com"]
