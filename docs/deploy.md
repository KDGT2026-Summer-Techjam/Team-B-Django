# デプロイ手順（Render）

担当: リーダー
**この手順書の目的は、リーダー以外でも再デプロイできる状態を保つことです。** 設定を変えたらこのファイルも更新を行います。

---

## 環境情報

| 項目 | 値 |
| --- | --- |
| 本番URL | https://seasonhub-web.onrender.com |
| Render サービス名 | seasonhub-web |
| DB | Supabase（無料プラン・PostgreSQL） |
| リージョン | Singapore |

---

## 0. Blueprint（render.yaml）を使ったデプロイ（推奨）

リポジトリ直下の `render.yaml` に Web Service（`seasonhub-web`）の設定を定義済みです。
DB は Render ではなく **Supabase** を使うため、`render.yaml` には DB を定義していません（経緯は「1. PostgreSQL」参照）。
Render ダッシュボードで以下を行うと、Build/Start Command・環境変数（`SECRET_KEY` の生成含む）が自動設定されます。**`DATABASE_URL` だけは手動で設定します。**

1. Render ダッシュボード → **New** → **Blueprint**
2. このリポジトリを選択（GitHub 連携が必要）
3. `render.yaml` の内容が読み込まれるので、内容を確認して **Apply**
4. `seasonhub-web` の Environment で、`DATABASE_URL` に Supabase の接続文字列を設定する（「2. 環境変数」参照）
5. 初回デプロイが完了したら、本番URLをこのファイルと `README.md` に追記する

`render.yaml` を変更した場合は、Render ダッシュボードで再度 Blueprint を反映（Sync）してください。
以下の「1. Render 側の設定」以降は、Blueprint を使わず手動でセットアップする場合の手順です。

---

## 1. Render 側の設定

### Web Service

| 項目 | 値 |
| --- | --- |
| Runtime | Python 3 |
| Build Command | `pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate` |
| Start Command | `gunicorn config.wsgi:application` |
| Instance Type | Free |

> `config` の部分は `settings.py` があるディレクトリ名です。プロジェクト名に合わせて読み替えてください。
> **`migrate` を Build Command に入れておく**と、デプロイのたびに自動でテーブルが更新されます。手動実行を忘れて 500 になる事故を防げます。

### PostgreSQL（Supabase）

DB は **Supabase の無料プラン**を使います。Supabase のプロジェクトを作成し、**Pooler の接続文字列**（Connect → Connection string）を控えます。

- 当初は Render の無料 PostgreSQL を使っていましたが、**作成から30日で失効し、その後削除される**ため（2026-10-23 に削除済みを確認）、Supabase に移行しました。削除されたDBは復元できません。
- Supabase の無料プランは、**7日間アクセスがないと自動で停止（Paused）**します。停止した場合は、Supabase のダッシュボードで **Resume project** を押すと再開できます。再開するまでは、デプロイ時の `migrate` が接続できずに失敗します。
- 接続文字列には**パスワードが含まれる**ため、リポジトリやドキュメントには書かず、Render の Environment にだけ設定します。

---

## 2. 環境変数

Render の Environment に以下を設定します。

| キー | 値 | 備考 |
| --- | --- | --- |
| `SECRET_KEY` | ランダムな文字列 | ローカルと別の値にする |
| `DEBUG` | `False` | **本番で True にしない** |
| `DATABASE_URL` | Supabase の接続文字列（Pooler） | Supabase の Connect からコピー。`render.yaml` では `sync: false`（手動設定） |
| `ALLOWED_HOSTS` | `.onrender.com` | 入れ忘れると全リクエストが 400 |
| `PYTHON_VERSION` | `3.12.4` | 明示しないと想定外のバージョンが使われる。開発環境（`.python-version`）と揃える |

`SECRET_KEY` の生成:

```bash
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

---

## 3. settings.py 側で必要な対応

```python
import os
import dj_database_url

DEBUG = os.environ.get("DEBUG", "False") == "True"
SECRET_KEY = os.environ["SECRET_KEY"]
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS", "").split(",")

DATABASES = {
    "default": dj_database_url.config(conn_max_age=600)
}

# 静的ファイルはバックエンドから配信する（デプロイ先を分けない）
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}

# HTTPS 経由であることを Render のプロキシから受け取る
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
CSRF_TRUSTED_ORIGINS = ["https://*.onrender.com"]
```

`MIDDLEWARE` の**上から2番目**（`SecurityMiddleware` の直後）に追加:

```python
"whitenoise.middleware.WhiteNoiseMiddleware",
```

> **`DEBUG = False` にすると Django 単体では静的ファイルを配信しません。**
> CSS が当たらない・画像が出ない場合はここを疑ってください。

---

## 4. デプロイの流れ

`main` ブランチへのマージで自動デプロイされます。

1. Pull Request をマージ
2. Render の Logs で `Build successful` を確認
3. 本番URLを開いて動作確認
4. #進捗共有 に「デプロイしました」と一言

手動で再デプロイする場合は、Render のダッシュボードから **Manual Deploy → Deploy latest commit**。

---

## 5. 発表当日（8/28）のチェックリスト

- [ ] **発表の30分前に本番URLへアクセスして起こしておく**（無料枠はスリープする。復帰に1分近くかかる）
- [ ] デモ用の投稿データを作成しておく（空の画面から始めない）
- [ ] 参加者が2〜3人入った状態の投稿を用意しておく
- [ ] QRコードを表示する準備（審査員にその場で参加ボタンを押してもらう）
- [ ] 会場のネットワークで本番URLが開けるか確認

---

## トラブル対応

### 400 Bad Request

`ALLOWED_HOSTS` に本番ドメインが入っていません。環境変数を確認してください。

### 500 Internal Server Error

Render の Logs を見ます。多いのは以下の2つです。

- `migrate` が走っていない → Build Command を確認
- 環境変数の未設定 → `KeyError: 'SECRET_KEY'` などが出ます

`DEBUG = True` に一時的に戻せば原因が画面に出ますが、**確認後は必ず False に戻すこと。**

### CSS が当たらない / 静的ファイルが 404

`collectstatic` が走っていないか、WhiteNoise が MIDDLEWARE に入っていません。

### 初回アクセスが極端に遅い

スリープからの復帰です。仕様なので直りません。**デモ前に起こしておくことで回避します。**

### DB のデータが消えた

無料プランの制約か、DB を作り直した可能性があります。**本番DBにはデモ用データしか置かないこと**を前提に運用してください。

---

## リーダー不在時

上記の手順と Render のアクセス権があれば、他のメンバーでも再デプロイできます。
**Render のアカウント共有方法を初日に決めて、ここに追記してください。**

- アクセスできる人: （ここを埋める）
- 共有方法: （ここを埋める）
