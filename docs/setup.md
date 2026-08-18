# 環境構築手順

初めてこのリポジトリを触るときに、上から順に実行してください。
**詰まったら30分以内に #質問・相談 に投げること。** 同じ場所で複数人が止まっていることが多いです。

---

## 0. 必要なもの

| ツール | バージョン | 確認コマンド |
| --- | --- | --- |
| Python | 3.11 以上 | `python --version` |
| Git | 任意 | `git --version` |
| PostgreSQL | ローカルで動かす場合のみ | `psql --version` |

> Python が `python3` でしか動かない環境（Mac / Linux）では、以下のコマンドの `python` を `python3` に読み替えてください。

---

## 1. クローン

```bash
git clone <リポジトリURL>
cd <リポジトリ名>
```

---

## 2. 仮想環境をつくる

**必ず仮想環境の中で作業してください。** グローバルに入れると他のプロジェクトを壊します。

```bash
# Mac / Linux
python3 -m venv venv
source venv/bin/activate

# Windows (PowerShell)
python -m venv venv
venv\Scripts\Activate.ps1
```

プロンプトの先頭に `(venv)` が付いていれば成功です。
**ターミナルを開き直すたびに `activate` が必要**なので忘れずに。

---

## 3. パッケージを入れる

```bash
pip install -r requirements.txt
```

`requirements.txt` に入っているもの:

- `Django` … 本体
- `psycopg2-binary` … PostgreSQL 接続
- `python-dotenv` … `.env` の読み込み
- `dj-database-url` … `DATABASE_URL` の解釈
- `whitenoise` … 静的ファイル配信（本番用）
- `gunicorn` … 本番サーバー（本番用）

---

## 4. `.env` を置く

**`.env` は Git に入っていません。** リーダーから受け取って、リポジトリの直下に置いてください。

```
SECRET_KEY=（リーダーから受け取る）
DEBUG=True
DATABASE_URL=（リーダーから受け取る）
```

> `.env` は絶対にコミットしないこと。`.gitignore` に入っていることを一度確認してください。

---

## 5. マイグレーション

```bash
python manage.py migrate
```

テーブル（`events` / `participants`）がDBに作られます。
**モデルを変更した人は、追加で以下も必要です。**

```bash
python manage.py makemigrations
python manage.py migrate
```

`makemigrations` で生成されたファイルは**コミットに含めてください**。含め忘れると他の人の環境でテーブルができません。

---

## 6. 起動

```bash
python manage.py runserver
```

ブラウザで http://127.0.0.1:8000 を開いてホーム画面が出れば完了です。

---

## よくある詰まり

### `ModuleNotFoundError: No module named 'django'`

仮想環境が有効になっていません。`activate` からやり直してください。

### `django.db.utils.OperationalError: could not connect to server`

`DATABASE_URL` が間違っているか、ローカルの PostgreSQL が起動していません。
まず `.env` の値をリーダーに確認してください。

### `ImproperlyConfigured: The SECRET_KEY setting must not be empty`

`.env` が読み込まれていません。ファイルの場所（リポジトリ直下か）と、ファイル名が `.env` になっているか（`env.txt` になっていないか）を確認してください。

### マイグレーションが衝突した

他の人の `makemigrations` と番号がぶつかっています。自分の migration ファイルを消して `git pull` し、もう一度 `makemigrations` してください。**自己判断で解決せず、先に共有すること。**

### 403 Forbidden (CSRF verification failed)

フロントから POST したときに出ます。CSRF の扱いはプロジェクト共通の決めごとなので、`/docs/設計.md` を確認してください。

---

## 作業の始め方

```bash
git switch main
git pull
git switch -c feature/機能名
```

- `main` に直接 Push しない
- 作業は `feature/機能名` ブランチ
- Pull Request → レビュー → マージ
- 担当ファイルは分かれているので、**自分の担当外のファイルは触らない**（コンフリクト防止）
