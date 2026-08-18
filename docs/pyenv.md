# pyenv 導入手順

チーム全員のPythonバージョンを **3.12.4** に統一するための手順。
このリポジトリには `.python-version`（`3.12.4`）が置いてあるため、pyenvを導入すれば `cd` するだけで自動的に切り替わります。

---

## Mac

```bash
brew install pyenv
```

シェルの設定ファイル（`~/.zshrc` など。bashなら `~/.bash_profile`）に以下を追記:

```bash
eval "$(pyenv init -)"
```

追記後、ターミナルを再起動（または `source ~/.zshrc`）してから:

```bash
pyenv install 3.12.4
```

---

## Windows

[pyenv-win](https://github.com/pyenv-win/pyenv-win) を使います。PowerShellを**管理者権限で**開いて実行:

```powershell
Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
```

インストール後、PowerShellを開き直してから:

```powershell
pyenv install 3.12.4
```

> 実行ポリシーのエラーが出る場合は `Set-ExecutionPolicy RemoteSigned -Scope CurrentUser` を先に実行してください。

---

## Linux（Ubuntu/Debian系）

ビルドに必要なパッケージを先に入れます:

```bash
sudo apt update
sudo apt install -y build-essential libssl-dev zlib1g-dev libbz2-dev \
  libreadline-dev libsqlite3-dev curl git libncursesw5-dev xz-utils \
  tk-dev libxml2-dev libxmlsec1-dev libffi-dev liblzma-dev
```

pyenv本体のインストール:

```bash
curl https://pyenv.run | bash
```

シェルの設定ファイル（`~/.bashrc` など）に以下を追記:

```bash
export PYENV_ROOT="$HOME/.pyenv"
command -v pyenv >/dev/null || export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
```

追記後、ターミナルを再起動（または `source ~/.bashrc`）してから:

```bash
pyenv install 3.12.4
```

---

## 確認

どのOSでも、インストール後にリポジトリのディレクトリで以下を実行して `3.12.4` と出れば成功です。

```bash
cd Team-B-Django
python --version
```

`.python-version` を読んで自動的に切り替わるので、`pyenv local` などは実行不要です。

### うまく切り替わらないとき

- `pyenv versions` で `3.12.4` がインストール済みか確認する
- シェルの設定ファイルへの追記後、ターミナルを再起動し忘れていないか確認する
- `python --version` が変わらない場合、`which python`（Windowsは `where python`）で参照先がpyenv配下のパスになっているか確認する

---

## 既存の仮想環境（venv）を使っている場合

`.python-version` を導入しても、**既存の `venv` フォルダのPythonバージョンは変わりません。** 作り直してください。

```bash
rm -rf venv
python -m venv venv
source venv/bin/activate   # Windowsは venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
