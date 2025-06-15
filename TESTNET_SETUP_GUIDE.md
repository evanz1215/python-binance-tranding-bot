# Binance Testnet API 金鑰設定說明

## 🔑 獲取 Testnet API 金鑰

### 1. 現貨 Testnet
1. 訪問: https://testnet.binance.vision/
2. 使用 GitHub 賬號登入
3. 建立 API 金鑰
4. 記錄 API Key 和 Secret Key

### 2. 合約 Testnet  
1. 訪問: https://testnet.binancefuture.com/
2. 使用 GitHub 賬號登入
3. 建立 API 金鑰
4. 記錄 API Key 和 Secret Key

## 📝 配置 .env 檔案

將獲得的 API 金鑰配置到 `.env` 檔案中：

```env
# Testnet 現貨 API 金鑰
BINANCE_SPOT_API_KEY=your_spot_testnet_api_key_here
BINANCE_SPOT_SECRET_KEY=your_spot_testnet_secret_key_here

# Testnet 合約 API 金鑰  
BINANCE_FUTURES_API_KEY=your_futures_testnet_api_key_here
BINANCE_FUTURES_SECRET_KEY=your_futures_testnet_secret_key_here

# 其他設定
BINANCE_TESTNET=true
TRADING_MODE=futures  # 可選: spot, futures, both
```

## 🧪 測試配置

運行診斷工具來測試你的 API 金鑰配置：

```bash
cd d:\Project\repos\python-binance-tranding-bot
uv run diagnose_api_keys.py
```

## ⚙️ 交易模式選擇

在 `.env` 檔案中設定 `TRADING_MODE`：

- `spot`: 只使用現貨交易
- `futures`: 只使用合約交易（推薦）
- `both`: 同時支援現貨和合約

## 🔧 常見問題

### 1. API 權限錯誤 (code=-2015)
- 檢查 API 金鑰是否正確
- 確認 API 金鑰已啟用相應的交易權限
- 檢查 IP 是否在白名單中

### 2. 時間戳錯誤 (code=-1021)
- 檢查系統時間是否同步
- 在 Windows 上可以運行: `w32tm /resync`

### 3. 沒有測試資金
- 現貨 testnet: 在個人頁面可以獲取測試 BTC 和 USDT
- 合約 testnet: 在個人頁面可以獲取測試 USDT

## 📋 API 權限要求

### 現貨交易需要的權限:
- ✅ 讀取 (Read)
- ✅ 現貨交易 (Spot Trading)

### 合約交易需要的權限:
- ✅ 讀取 (Read)  
- ✅ 合約交易 (Futures Trading)

## 🚀 啟動交易機器人

配置完成後，可以啟動 API 服務器：

```bash
cd d:\Project\repos\python-binance-tranding-bot
uv run main.py api
```

然後訪問 http://localhost:8000 查看儀表板。
