# Pythonリリース情報スクレイパー

スクリプトプログラミング演習2 加点用の独立プロジェクトです。

- 学籍番号: HW25A066
- 氏名: 嶋田一歩
- GitHubリポジトリ: `ypkabu/HW25A066-script-programming2-python-release-scraper`
- Jenkinsジョブ: `HW25A066-python-release-scraper`

## 内容

Python公式サイト `https://www.python.org/downloads/source/` から最近のPythonリリース情報を取得し、以下を生成します。

- `output/releases.json`
- `output/releases.csv`
- `output/index.html`
- `output/build_summary.json`
- `output/artifact_manifest.json`

取得項目はバージョン、公開日、詳細URLです。ネットワーク失敗時は `data/python_releases_fixture.html` を使用します。

## ローカル実行

```powershell
python run_local.py --offline
```

実際にpython.orgへ接続する場合:

```powershell
python run_local.py
```

## Jenkins / GitHub / ngrok

Jenkinsでは Pipeline from SCM として `Jenkinsfile` を指定します。

- ジョブ名: `HW25A066-python-release-scraper`
- GitHub push trigger: `githubPush()`
- GitHub Webhook Payload URL: `https://<ngrokのURL>/github-webhook/`
- ngrok起動例: `ngrok http 8080`
- 成果物: `output/**` をarchive

## Discord通知

Webhook URLはソースに書きません。Jenkins CredentialsのSecret textに保存し、パラメータ `DISCORD_CREDENTIAL_ID`（既定: `discord-webhook-url`）で参照します。未設定時や通知失敗時は安全にスキップします。

通知内容:

- ジョブ名
- ビルド番号
- SUCCESS / FAILURE
- Gitコミット
- ビルドURL
