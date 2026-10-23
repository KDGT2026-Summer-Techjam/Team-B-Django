"""本番設定（DEBUG=False）のセキュリティ設定が、check --deploy で警告なしになることを確認する。

テスト実行中は settings.py の本番用の設定（`if not DEBUG and not TESTING:`）が無効になるため、
本番の設定そのものを別プロセス（manage.py check --deploy）で読み込んで確認する。
"""

import os
import secrets
import subprocess
import sys
from pathlib import Path

from django.test import SimpleTestCase

BASE_DIR = Path(__file__).resolve().parent.parent


def run_check_deploy(debug: str) -> subprocess.CompletedProcess:
    """指定した DEBUG の値で `manage.py check --deploy` を別プロセスで実行する。"""
    env = {
        key: value
        for key, value in os.environ.items()
        if key not in ("DATABASE_URL", "SECRET_KEY", "DEBUG", "ALLOWED_HOSTS")
    }
    env["DEBUG"] = debug
    # W009（SECRET_KEYの強度）の確認用に、毎回ランダムな十分に長い値を使う（実際の値ではない）。
    env["SECRET_KEY"] = secrets.token_urlsafe(64)
    env["ALLOWED_HOSTS"] = "seasonhub-web.onrender.com"
    return subprocess.run(
        [sys.executable, "manage.py", "check", "--deploy"],
        cwd=BASE_DIR,
        env=env,
        capture_output=True,
        text=True,
        timeout=60,
    )


class ProductionSecuritySettingsTests(SimpleTestCase):
    def test_production_settings_have_no_deploy_warnings(self):
        """DEBUG=False（本番）では、check --deploy の警告が出ない。"""
        result = run_check_deploy(debug="False")
        output = result.stdout + result.stderr  # 警告は標準エラー出力に出る

        self.assertEqual(result.returncode, 0, output)
        self.assertIn("System check identified no issues", output)

    def test_debug_true_does_not_apply_production_settings(self):
        """DEBUG=True（ローカル開発）では本番用の設定が効かず、これまでどおり警告が出る。

        ローカルがHTTPS必須になって、http://localhost で開発できなくなることを防ぐ確認。
        """
        result = run_check_deploy(debug="True")
        output = result.stdout + result.stderr

        self.assertIn("security.W008", output)
        self.assertIn("security.W018", output)
