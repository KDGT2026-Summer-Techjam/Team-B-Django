# Inby（インビー）

**季節イベントに誘ってデコる。**

> 季節のイベントへの誘いを、参加確認・人数把握までまとめて済ませられるWebアプリ。

**イベントの誘いを共有URLつきで作成し、受け取った人が名前を入れて参加ボタンを押すだけで意思表示できる。**
インストール不要・アカウント登録不要。リンクを開くだけで使えます。

- 本番URL: https://seasonhub-web.onrender.com
- 開発期間: 2026年8月18日 〜 8月28日（Techjam 2026夏）

---

## 解決する課題

高校生から20代前半の仲の良いグループで、季節のイベントやレジャーに行って共通の思い出を残したい人向け。

- 友達と遊びに行った後、膨大な量の写真を確認するのが大変
- 普通に写真を撮って友達と後から送り合うだけでは味気ない

**そのイベントの全体像が一目で見えて、かつオリジナルの画像を簡単に作って共有できるようにする。**

---

## 使い方

1. ホームから「誘いを作成」でイベント名・日付・場所を入力する
2. 生成された共有文をコピーして、LINEなどに貼る
3. リンクを受け取った人がページを開き、名前を入れて参加ボタンを押す
4. 作成者の画面に参加者が増えていく

参加する側にアカウントは要りません。リンクを開いて名前を入れるだけです。

---

## 技術スタック

| 領域 | 使用技術 |
| --- | --- |
| バックエンド | Python / Django |
| フロントエンド | Vanilla JS（HTML / CSS / JS） |
| DB | PostgreSQL |
| デプロイ | Render |

---

## 開発環境の構築

[docs/setup.md](docs/setup.md) を参照してください。

```bash
git clone <リポジトリURL>
cd <リポジトリ名>
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# .env をリポジトリ直下に配置（リーダーから受け取る）
python manage.py migrate
python manage.py runserver
```

---

## ドキュメント

| ファイル | 内容 |
| --- | --- |
| [docs/要件定義.md](docs/要件定義.md) | 課題・ターゲット・MVP・機能一覧（Must / Should / Could） |
| [docs/設計.md](docs/設計.md) | 画面構成・UI仕様・URL設計・API仕様・DB設計 |
| [docs/開発計画.md](docs/開発計画.md) | スケジュール・体制・開発ルール・完成条件 |
| [docs/setup.md](docs/setup.md) | 環境構築手順 |
| [docs/deploy.md](docs/deploy.md) | デプロイ手順（Render） |
| [docs/pr-guide.md](docs/pr-guide.md) | PR作成手順書 |

---

## フォルダ構成

```text
Team-B-Django/
├── README.md              # このファイル
├── manage.py              # Django管理コマンドの実行入口
├── requirements.txt       # 依存パッケージ一覧
├── render.yaml            # Renderへのデプロイ設定
├── config/                # プロジェクト設定
│   ├── settings.py        # Django設定（DB接続・ミドルウェア登録など）
│   ├── urls.py            # 全体のURLルーティングの入口
│   ├── asgi.py
│   └── wsgi.py
├── events/                # イベント機能アプリ
│   ├── models.py          # DBモデル（Event, Participant）
│   ├── urls.py             # 画面URL・API URLの定義
│   ├── views_pages.py     # 各画面（HTML）を描画するビュー
│   ├── views_api.py       # フロントJSから叩くJSON API
│   ├── middleware.py      # visitor_id発行のミドルウェア
│   ├── tests.py           # テストコード
│   └── migrations/        # DBマイグレーションファイル
├── templates/
│   └── events/            # 各画面のHTMLテンプレート
│       ├── home.html
│       ├── new_event.html
│       ├── event_page.html
│       ├── event_done.html
│       ├── event_edit.html
│       ├── my_events.html
│       └── error.html
└── docs/                  # ドキュメント
    ├── 要件定義.md
    ├── 設計.md
    ├── 開発計画.md
    ├── setup.md
    ├── deploy.md
    └── pr-guide.md
```

### 主要ファイルの役割

| ファイル | 役割 |
| --- | --- |
| [config/urls.py](config/urls.py) | 全体のURLルーティングの入口。`events/urls.py`を読み込み、404時は`error_page`に振り分け |
| [config/settings.py](config/settings.py) | Django設定（DB接続・ミドルウェア登録など） |
| [events/urls.py](events/urls.py) | 画面URL（`/`, `/new`, `/e/<public_id>/` 等）とAPI URL（`/api/events/...`）の定義 |
| [events/views_pages.py](events/views_pages.py) | 各画面（HTML）を描画するビュー。`home` `new_event` `event_page` `event_done` `event_edit` `my_events_list` `error_page` |
| [events/views_api.py](events/views_api.py) | フロントJSから叩くJSON API。`create_event`（作成） `get_event`（詳細取得） `join_event`（参加登録） |
| [events/models.py](events/models.py) | DBモデル。`Event`（イベント本体、`public_id`と`edit_token`を自動発行） `Participant`（参加者） |
| [events/middleware.py](events/middleware.py) | 初回アクセス時に`visitor_id`をCookie発行し、参加済み判定や自分のイベント一覧の識別に使う |
| [events/migrations/](events/migrations/) | モデル変更を反映するDBマイグレーションファイル |
| [templates/events/home.html](templates/events/home.html) | トップページ。「誘いを作成」への導線 |
| [templates/events/new_event.html](templates/events/new_event.html) | イベント作成フォーム（タイトル・日付・場所・投稿者名） |
| [templates/events/event_page.html](templates/events/event_page.html) | 誘いのページ。イベント情報表示＋参加者一覧＋参加ボタン |
| [templates/events/event_done.html](templates/events/event_done.html) | 作成完了画面。共有用URLの表示・コピー |
| [templates/events/event_edit.html](templates/events/event_edit.html) | イベント編集フォーム |
| [templates/events/my_events.html](templates/events/my_events.html) | 自分が作成・参加したイベントの一覧 |
| [templates/events/error.html](templates/events/error.html) | 404などのエラー表示画面 |
| [manage.py](manage.py) | Django管理コマンドの実行入口（`runserver` `migrate` 等） |
| [render.yaml](render.yaml) | Renderへのデプロイ設定 |

---

## 担当

| 役割 | 人数 | 担当者 |
| --- | --- | --- |
| PM / デプロイ | 1 | @Karuhito |
| フロントエンド | 2 | @amano02 @jinki827 |
| バックエンド | 2 | @rs0325 @mudesu |

---

## 開発ルール

- `main` ブランチへの直接Pushは禁止
- 作業は `feature/機能名` ブランチで行い、Pull Request → レビュー → マージ
- タスクはGitHub Issueで管理（タイトルは「動詞＋対象」、担当者をAssigneesに設定）
- ラベルで Must / Should / Could を分類
- 詰まったら30分以内に相談する
