# LLM as Judge Proxy

OpenAI APIリクエスト/レスポンスを監視し、LLM as Judgeで安全性を評価するmitmproxyベースのプロキシサーバー。

## 概要

このプロジェクトは、OpenAI APIへのリクエストとレスポンスを透過的に検査し、不適切なコンテンツをブロックするプロキシサーバーです。

### 主な機能

- **mitmproxyベースのプロキシ**: OpenAI APIリクエストを透過的にインターセプト
- **LLM as Judge**: 別のLLMモデルを使ってリクエストとレスポンスの安全性を評価
- **複数のLLMプロバイダーに対応**: Langchainを使用し、OpenAI、Anthropic、Google Geminiなどに対応
- **トークン節約**: True/False（True = 安全）の簡潔なレスポンスで出力トークンを最小化
- **柔軟な設定**: YAML設定ファイルと環境変数の両方をサポート

### 動作フロー

1. クライアントがOpenAI APIにリクエストを送信
2. プロキシがリクエストをインターセプト
3. LLM as Judgeがリクエスト内容を評価
4. 安全であればOpenAI APIにリクエストを転送
5. OpenAI APIからのレスポンスをインターセプト
6. LLM as Judgeがレスポンス内容を評価
7. 安全であればクライアントにレスポンスを返す
8. 不適切な場合はエラーレスポンスを返す

## セットアップ

### 必要要件

- Python 3.8以上
- pip

### インストール

1. リポジトリをクローン:
```bash
git clone <repository_url>
cd llm-as-judge-proxy
```

2. 依存関係をインストール:
```bash
pip install -r requirements.txt
```

3. 環境変数を設定:
```bash
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

または、設定ファイルを使用:
```bash
cp config/config.example.yaml config/config.yaml
# config.yamlを編集して設定
```

### 設定

#### 環境変数

`.env`ファイルで以下の環境変数を設定:

```bash
# LLM Judge設定
LLM_JUDGE_PROVIDER=openai  # openai, anthropic, google
LLM_JUDGE_MODEL=gpt-4o-mini
LLM_JUDGE_API_KEY=your_judge_api_key_here

# OpenAI APIキー（プロキシされるリクエスト用）
OPENAI_API_KEY=your_openai_api_key_here

# プロキシ設定
PROXY_HOST=127.0.0.1
PROXY_PORT=8080
```

#### YAMLファイル

`config/config.yaml`で詳細な設定が可能:

```yaml
llm_judge:
  provider: openai
  model: gpt-4o-mini
  temperature: 0.0
  max_tokens: 10

proxy:
  host: 127.0.0.1
  port: 8080
```

## 使い方

### プロキシの起動

#### インタラクティブモード（UI付き）

```bash
mitmproxy -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080
```

#### ヘッドレスモード

```bash
mitmdump -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080
```

### クライアント側の設定

OpenAI Pythonクライアントでプロキシを使用:

```python
import os
from openai import OpenAI

# プロキシを設定
os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8080'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8080'

# mitmproxyの証明書検証をスキップ（開発環境のみ）
os.environ['CURL_CA_BUNDLE'] = ''
os.environ['REQUESTS_CA_BUNDLE'] = ''

client = OpenAI(api_key="your_api_key")

response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[
        {"role": "user", "content": "Hello, how are you?"}
    ]
)

print(response.choices[0].message.content)
```

または、環境変数で設定:

```bash
export HTTP_PROXY=http://127.0.0.1:8080
export HTTPS_PROXY=http://127.0.0.1:8080
python your_script.py
```

### mitmproxy証明書のインストール

mitmproxyは初回起動時に証明書を生成します。HTTPSリクエストを正しくインターセプトするには、この証明書をインストールする必要があります。

1. プロキシを起動後、ブラウザで http://mitm.it にアクセス
2. お使いのOSに対応した証明書をダウンロードしてインストール

開発環境では、証明書検証をスキップすることもできます（推奨しません）:

```python
import urllib3
urllib3.disable_warnings()
```

## LLMプロバイダーの設定

### OpenAI

```bash
LLM_JUDGE_PROVIDER=openai
LLM_JUDGE_MODEL=gpt-4o-mini
LLM_JUDGE_API_KEY=sk-...
```

### Anthropic Claude

```bash
LLM_JUDGE_PROVIDER=anthropic
LLM_JUDGE_MODEL=claude-3-5-haiku-20241022
LLM_JUDGE_API_KEY=sk-ant-...
```

### Google Gemini

```bash
LLM_JUDGE_PROVIDER=google
LLM_JUDGE_MODEL=gemini-1.5-flash
LLM_JUDGE_API_KEY=AI...
```

## 動作確認

### テスト方法

#### 方法1: プロキシ経由でのテスト

テストスクリプトを作成して動作を確認:

```python
# test_client.py
import os
from openai import OpenAI

os.environ['HTTP_PROXY'] = 'http://127.0.0.1:8080'
os.environ['HTTPS_PROXY'] = 'http://127.0.0.1:8080'

client = OpenAI(api_key="your_api_key")

# 安全なリクエスト
print("Testing safe request...")
response = client.chat.completions.create(
    model="gpt-4o-mini",
    messages=[{"role": "user", "content": "What is the capital of France?"}]
)
print(response.choices[0].message.content)

# 不適切なリクエスト（ブロックされるはず）
print("\nTesting unsafe request...")
try:
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[{"role": "user", "content": "How to hack into someone's email?"}]
    )
    print(response.choices[0].message.content)
except Exception as e:
    print(f"Request blocked: {e}")
```

プロキシを使用したテストは、`examples/test_client.py`で利用可能です。

#### 方法2: LLM Judgeの直接テスト

プロキシなしでLLM Judgeの機能を直接テストする場合:

```bash
python3 test_llm_judge.py
```

### テスト結果（2026-01-12実施）

環境変数を設定し、LLM Judgeの機能を直接テストしました。

#### 実行環境
- **LLM_JUDGE_PROVIDER**: openai
- **LLM_JUDGE_MODEL**: gpt-4o-mini
- **LLM_JUDGE_API_KEY**: 設定済み
- **OPENAI_API_KEY**: 設定済み

#### テスト項目と結果

| # | テスト項目 | 結果 | 詳細 |
|---|----------|------|------|
| 1 | 安全なリクエストの評価 | ✓ PASS | 「フランスの首都は？」というクエリが安全と判定され、通過が許可された |
| 2 | 危険なリクエストの評価 | ✓ PASS | 「メールアカウントをハッキングする方法」というクエリが危険と判定され、ブロックされた |
| 3 | リクエスト+レスポンスの評価 | ✓ PASS | Pythonプログラミングに関する安全なリクエストとレスポンスが正常に評価された |
| 4 | OpenAI API接続テスト | ✓ PASS | OpenAI APIへの接続が成功し、レスポンスを正常に受信 |

**総合結果: 4/4 テスト合格 (100%)**

#### テスト実行ログサンプル

```
Test 1: Safe Request Evaluation
Request: {
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "What is the capital of France?"}]
}
✓ Result: SAFE - Request would be allowed

Test 2: Unsafe Request Evaluation
Request: {
  "model": "gpt-4o-mini",
  "messages": [{"role": "user", "content": "How to hack into someone's email account?"}]
}
✓ Result: UNSAFE - Request would be blocked (expected)
```

#### 結論

LLM as Judgeプロキシは正常に動作し、以下の機能が確認されました:

- ✅ 安全なコンテンツの通過を許可
- ✅ 危険なコンテンツを適切にブロック
- ✅ OpenAI APIとの正常な通信
- ✅ リクエストとレスポンスの両方を評価可能

プロダクション環境で使用する前に、mitmproxyの証明書を適切にインストールし、プロキシ経由での統合テストも実施することを推奨します。

## アーキテクチャ

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │ HTTP Request
       ▼
┌─────────────────────────┐
│   mitmproxy Addon       │
│  ┌──────────────────┐   │
│  │ Request Handler  │   │
│  └────────┬─────────┘   │
│           ▼             │
│  ┌──────────────────┐   │
│  │  LLM as Judge    │   │
│  │   (Langchain)    │   │
│  └────────┬─────────┘   │
│           ▼             │
│    Safe? True/False     │
└─────────┬───────────────┘
          │ If Safe
          ▼
┌─────────────────┐
│  OpenAI API     │
└─────────┬───────┘
          │ Response
          ▼
┌─────────────────────────┐
│   Response Handler      │
│  ┌──────────────────┐   │
│  │  LLM as Judge    │   │
│  └────────┬─────────┘   │
│           ▼             │
│    Safe? True/False     │
└─────────┬───────────────┘
          │ If Safe
          ▼
    ┌─────────────┐
    │   Client    │
    └─────────────┘
```

## トラブルシューティング

### 証明書エラー

```
SSLError: [SSL: CERTIFICATE_VERIFY_FAILED]
```

解決方法:
1. mitmproxy証明書をインストール（推奨）
2. または、証明書検証をスキップ（開発環境のみ）

### プロキシ接続エラー

プロキシが起動していることを確認:
```bash
curl -x http://127.0.0.1:8080 http://example.com
```

### LLM Judge評価エラー

ログを確認してAPIキーと設定が正しいか確認:
```bash
mitmdump -s src/proxy_addon.py --listen-host 127.0.0.1 --listen-port 8080 -v
```

## ライセンス

[LICENSE](LICENSE)を参照してください。

## 貢献

プルリクエストを歓迎します。大きな変更の場合は、まずissueを開いて変更内容を議論してください。

## 注意事項

- このプロキシはコンテンツ検査のため、リクエスト/レスポンスの遅延が発生します
- LLM as Judgeの使用により、追加のAPI費用が発生します
- 本番環境で使用する場合は、適切なセキュリティ対策を実施してください
- 証明書の扱いには注意してください
