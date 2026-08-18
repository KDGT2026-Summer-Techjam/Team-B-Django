# 環境構築手順

初めてこのリポジトリを触るときに、上から順に実行してください。
**詰まったら30分以内に #質問・相談 に投げること。** 同じ場所で複数人が止まっていることが多いです。

---

## 0. 必要なもの

| ツール | バージョン | 確認コマンド |
| --- | --- | --- |
| Python | 3.11 以上 | `python --version` |
| Git | 任意 | `git --version` |
| PostgreSQL | 必須（各自のPCにインストール） | `psql --version` |

> Python が `python3` でしか動かない環境（Mac / Linux）では、以下のコマンドの `python` を `python3` に読み替えてください。

---

## 1. クローン

```bash
git clone https://github.com/KDGT2026-Summer-Techjam/Team-B-Django
cd Team-B-Django
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

## 4. ローカルPostgreSQLのセットアップ

**DBは各自のPCに用意します（リーダーのDBを共有するわけではありません）。** OSに合わせて進めてください。

### Mac（Homebrew）

```bash
brew install postgresql@15
brew services start postgresql@15
createdb techjam_dev
```

Homebrew版はデフォルトでパスワードなしで自分のOSユーザー名のまま接続できます。

### Windows

1. [公式サイト](https://www.postgresql.org/download/windows/) からインストーラー（EDB版）をダウンロードして実行する
2. インストール中に **`postgres` ユーザーのパスワードを設定する画面が出るので、必ず控えておく**（後で使います。忘れると詰まります）
3. Port はデフォルトの `5432` のままでよい
4. インストール完了後、スタートメニューから **SQL Shell (psql)** を開く
5. `Server` `Database` `Port` `Username` は Enter で全てデフォルトのままにし、`Password` に手順2で設定したパスワードを入力する
6. 接続できたら、以下を実行してDBを作成する

   ```sql
   CREATE DATABASE techjam_dev;
   ```

7. `\q` で終了する

### Linux（Ubuntu/Debian系）

```bash
sudo apt install postgresql
sudo -u postgres createdb techjam_dev
sudo -u postgres psql -c "ALTER USER postgres WITH PASSWORD '任意のパスワード';"
```

### 動作確認

```bash
psql -h localhost -U <ユーザー名> -d techjam_dev -c "SELECT 1;"
```

エラーなく `1` が返れば接続できています。

---

## 5. `.env` を置く

**`.env` は Git に入っていません。** `SECRET_KEY` はリーダーから受け取ってください。`DATABASE_URL` は前の手順で作った**自分のローカルDBの接続情報**を自分で書きます。

```
SECRET_KEY=（リーダーから受け取る）
DEBUG=True
DATABASE_URL=postgres://<ユーザー名>:<パスワード>@localhost:5432/techjam_dev
ALLOWED_HOSTS=127.0.0.1,localhost
```

- Mac（Homebrew）でパスワードを設定していない場合は `postgres://<ユーザー名>@localhost:5432/techjam_dev` のように `:<パスワード>` の部分を省略してください
- Windows / Linux は手順4で設定したパスワードを入れてください

> `.env` は絶対にコミットしないこと。`.gitignore` に入っていることを一度確認してください。

---

## 6. マイグレーション

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

## 7. 起動

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
Windows は「サービス」アプリで `postgresql-x64-15` が起動しているか確認してください。Macは `brew services list` で `postgresql@15` が `started` になっているか確認してください。

### `FATAL: password authentication failed for user`

`.env` の `DATABASE_URL` に書いたパスワードが、DB作成時に設定したものと違います。手順4で控えたパスワードと見比べてください。
分からなくなった場合、Windowsは再インストールが一番早いです（アンインストール後、手順4からやり直す）。Mac/Linuxは `ALTER USER` でパスワードを設定し直してください。**自己判断でDBの認証設定ファイル（`pg_hba.conf`）を書き換えるのはリスクが高いので、先に #質問・相談 に投げること。**

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
