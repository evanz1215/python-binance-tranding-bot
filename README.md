# 🤖 Binance Auto Trading Bot

一個功能完整的Binance自動化交易機器人，支援多種交易策略、回測分析、風險管理和實時監控。

## ✨ 主要功能

### 🎯 交易策略
- **移動平均交叉策略** (MA Cross) - 經典的雙均線交叉策略
- **RSI策略** - 基於相對強弱指標的超買超賣策略 
- **MACD策略** - 基於MACD指標的趨勢跟隨策略
- **布林帶策略** - 基於布林帶的均值回歸策略
- **組合策略** - 結合多個技術指標的綜合策略
- **可擴展架構** - 輕鬆添加自定義策略

### 📊 數據管理
- 實時市場數據收集和存儲
- 多時間框架支援 (1m, 5m, 15m, 1h, 4h, 1d)
- 自動數據更新和歷史數據回填
- 數據清理和維護

### ⚠️ 風險管理
- 智能倉位管理和資金分配
- 停損和止盈自動執行
- 每日虧損限制和最大回撤保護
- 實時風險監控和警報
- 多層級風險評估系統

### 📈 回測系統
- 完整的歷史數據回測
- 詳細的績效分析報告
- 參數優化功能
- 多策略對比分析
- 風險指標計算 (Sharpe比率、最大回撤等)

### 🔍 智能幣種篩選
- 基於24小時交易量的自動篩選
- 白名單/黑名單過濾系統
- 動態監控熱門交易對
- 流動性和波動性分析

### 📱 監控和通知
- Web管理介面
- Telegram和Discord通知
- 實時交易執行通知
- 風險警報和系統狀態更新
- 每日交易總結報告

### 🛡️ 安全特性
- API密鑰安全存儲
- 測試網支援 (避免真實交易風險)
- 完整的錯誤處理和恢復機制
- 操作日誌和審計追蹤

## 🚀 快速開始

### 1. 安裝依賴

```bash
# 克隆專案
git clone <repository-url>
cd python-binance-trading-bot

# 安裝Python依賴
pip install -e .
```

### 2. 配置設定

```bash
# 複製環境變數範例檔案
cp .env.example .env

# 編輯 .env 檔案，添加您的Binance API密鑰
```

**重要配置項目：**
```bash
# Binance API配置
BINANCE_API_KEY=your_api_key_here
BINANCE_SECRET_KEY=your_secret_key_here
BINANCE_TESTNET=true  # 建議先在測試網測試

# 交易參數
POSITION_SIZE_PCT=0.1    # 每筆交易使用10%資金
STOP_LOSS_PCT=0.05       # 5%停損
TAKE_PROFIT_PCT=0.15     # 15%止盈
MAX_POSITIONS=10         # 最多同時持有10個倉位
```

### 3. 初始化數據庫

```bash
# 更新市場數據
python main.py update-data
```

### 4. 運行回測 (建議)

```bash
# 回測移動平均策略
python main.py backtest --strategy ma_cross --symbols BTCUSDT ETHUSDT --days 30

# 回測RSI策略
python main.py backtest --strategy rsi --symbols BTCUSDT ETHUSDT ADAUSDT --days 30
```

### 5. 啟動交易機器人

```bash
# 啟動實時交易 (請確保已在測試網測試)
python main.py trade --strategy ma_cross

# 啟動Web管理介面
python main.py api
```

然後訪問 http://localhost:8000 查看管理介面。

## 📋 詳細使用指南

### 命令行工具

```bash
# 查看所有可用命令
python main.py --help

# 交易命令
python main.py trade --strategy ma_cross --fast-period 12 --slow-period 26

# 回測命令  
python main.py backtest --strategy rsi --symbols BTCUSDT ETHUSDT --days 60

# 啟動API服務器
python main.py api --host 0.0.0.0 --port 8000

# 更新市場數據
python main.py update-data --symbols BTCUSDT ETHUSDT --timeframes 1h 4h

# 測試通知系統
python main.py test-notifications
```

### 策略配置

#### 移動平均交叉策略
```python
# 快速均線週期12，慢速均線週期26
python main.py trade --strategy ma_cross --fast-period 12 --slow-period 26
```

#### RSI策略
```python
# RSI週期14，超賣30，超買70
python main.py trade --strategy rsi --period 14 --oversold 30 --overbought 70
```

#### MACD策略
```python
# 快線12，慢線26，信號線9
python main.py trade --strategy macd --fast 12 --slow 26 --signal 9
```

### Web API使用

```bash
# 獲取機器人狀態
curl http://localhost:8000/api/status

# 獲取賬戶餘額
curl http://localhost:8000/api/balance

# 獲取當前倉位
curl http://localhost:8000/api/positions

# 獲取風險報告
curl http://localhost:8000/api/risk/report

# 啟動交易
curl -X POST http://localhost:8000/api/trading/start

# 停止交易
curl -X POST http://localhost:8000/api/trading/stop
```

## ⚙️ 配置參數說明

### 交易參數
- `POSITION_SIZE_PCT`: 每筆交易使用的資金比例 (0.1 = 10%)
- `MAX_POSITIONS`: 最大同時持倉數量
- `STOP_LOSS_PCT`: 停損比例 (0.05 = 5%)
- `TAKE_PROFIT_PCT`: 止盈比例 (0.15 = 15%)
- `MIN_VOLUME_24H`: 最小24小時交易量篩選

### 風險管理
- `MAX_DAILY_LOSS_PCT`: 每日最大虧損限制
- `MAX_DRAWDOWN_PCT`: 最大回撤限制

### 幣種篩選
- `SYMBOL_WHITELIST`: 白名單幣種 (僅交易指定幣種)
- `SYMBOL_BLACKLIST`: 黑名單幣種 (排除指定幣種)

## 📊 回測報告示例

```
==================================================
BACKTEST RESULTS
==================================================
Strategy: ma_cross
Period: 2024-05-15 to 2024-06-15
Initial Balance: $10,000.00
Final Balance: $11,250.00
Total Return: $1,250.00 (12.50%)
Max Drawdown: $580.00 (5.80%)
Sharpe Ratio: 1.85
Total Trades: 45
Win Rate: 62.22%
Profit Factor: 1.68
==================================================
```

## 🔔 通知設定

### Telegram設定
1. 創建Telegram機器人：與@BotFather對話
2. 獲取機器人Token
3. 獲取您的Chat ID
4. 在.env中設定：
```bash
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

### Discord設定
1. 在Discord服務器中創建Webhook
2. 複製Webhook URL
3. 在.env中設定：
```bash
DISCORD_WEBHOOK=your_webhook_url
```

## 📁 專案結構

```
python-binance-trading-bot/
├── src/
│   ├── __init__.py
│   ├── config.py              # 配置管理
│   ├── binance_client.py      # Binance API客戶端
│   ├── data_manager.py        # 數據管理
│   ├── risk_manager.py        # 風險管理
│   ├── trading_engine.py      # 交易引擎
│   ├── backtest_engine.py     # 回測引擎
│   ├── notifications.py       # 通知系統
│   ├── api.py                 # Web API
│   ├── database/              # 數據庫模型
│   │   ├── __init__.py
│   │   └── models.py
│   └── strategies/            # 交易策略
│       ├── __init__.py
│       └── base.py
├── main.py                    # 主程式入口
├── pyproject.toml            # 依賴配置
├── .env.example              # 環境變數範例
└── README.md                 # 說明文檔
```

## ⚠️ 風險提醒

- **測試優先**: 請務必先在Binance測試網進行充分測試
- **資金安全**: 僅使用您能承受損失的資金
- **監控重要**: 定期檢查機器人運行狀態和交易結果
- **策略理解**: 充分理解所使用的交易策略的風險和特性
- **市場風險**: 加密貨幣市場波動劇烈，過往績效不代表未來結果

## 🛠️ 開發和自定義

### 添加自定義策略

1. 在`src/strategies/base.py`中繼承`BaseStrategy`類
2. 實現必要的方法：`analyze()`, `get_required_timeframes()`, `get_required_periods()`
3. 在`STRATEGIES`字典中註冊新策略

### 擴展通知功能

1. 在`src/notifications.py`中添加新的通知渠道
2. 實現相應的發送方法
3. 在`NotificationManager`中整合新渠道

## 📄 授權條款

本專案採用MIT授權條款。詳情請參閱LICENSE文件。

## 🤝 貢獻

歡迎提交Issue和Pull Request來改進這個專案！

## 📞 支援

如果您遇到問題或需要幫助，請：
1. 查看文檔和常見問題
2. 在GitHub上提交Issue
3. 加入我們的社群討論

---

**免責聲明**: 本軟體僅供教育和研究目的。使用本軟體進行實際交易的所有風險由用戶自行承擔。開發者不對任何交易損失負責。