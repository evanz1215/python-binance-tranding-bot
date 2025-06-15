# 🚀 Binance 交易機器人 - 快速入門指南

## 步驟 1: 準備工作

### 1.1 系統要求
- Python 3.11 或更高版本
- 至少 4GB 記憶體
- 穩定的網路連接

### 1.2 Binance 帳戶設定
1. 註冊 Binance 帳戶：https://www.binance.com
2. 完成身份驗證
3. 創建 API 密鑰：
   - 登入 Binance → 用戶中心 → API 管理
   - 創建新的 API 密鑰
   - **重要**: 僅開啟現貨交易權限，不要開啟提現權限
   - 記錄 API Key 和 Secret Key

## 步驟 2: 安裝和配置

### 2.1 下載和安裝
```bash
# 1. 克隆專案
git clone <repository-url>
cd python-binance-trading-bot

# 2. 運行安裝腳本
python setup.py
```

### 2.2 配置 API 密鑰
編輯 `.env` 檔案：
```bash
# 將您的 API 密鑰填入
BINANCE_API_KEY=your_actual_api_key_here
BINANCE_SECRET_KEY=your_actual_secret_key_here

# 建議先用測試網
BINANCE_TESTNET=true
```

### 2.3 基本交易設定
```bash
# 交易參數（可根據需要調整）
POSITION_SIZE_PCT=0.05    # 每筆交易使用5%資金（較保守）
STOP_LOSS_PCT=0.03        # 3%停損
TAKE_PROFIT_PCT=0.10      # 10%止盈
MAX_POSITIONS=5           # 最多5個倉位
```

## 步驟 3: 首次測試

### 3.1 更新市場數據
```bash
python main.py update-data
```

### 3.2 運行回測（重要！）
```bash
# 測試移動平均策略
python main.py backtest --strategy ma_cross --days 30

# 測試 RSI 策略
python main.py backtest --strategy rsi --days 30
```

查看回測結果，確保策略有正收益再進行實盤交易。

### 3.3 測試通知系統（可選）
```bash
python main.py test-notifications
```

## 步驟 4: 開始交易

### 4.1 啟動 Web 介面（推薦）
```bash
python main.py api
```
然後訪問 http://localhost:8000 進行可視化管理。

### 4.2 或直接命令行交易
```bash
# 啟動移動平均策略
python main.py trade --strategy ma_cross
```

### 4.3 監控（另開終端）
```bash
python monitor.py
```

## 步驟 5: 安全檢查清單

### ✅ 交易前確認
- [ ] API 密鑰已正確設定
- [ ] 正在使用測試網 (BINANCE_TESTNET=true)
- [ ] 回測結果顯示正收益
- [ ] 風險參數設定合理
- [ ] 已設定停損和止盈
- [ ] 通知系統正常工作

### ✅ 實盤交易前確認
- [ ] 在測試網充分測試
- [ ] 理解策略的風險和特性
- [ ] 僅使用可承受損失的資金
- [ ] 設定了每日虧損限制
- [ ] 準備好監控交易狀況

## 常用命令

```bash
# 查看幫助
python main.py --help

# 更新數據
python main.py update-data

# 回測
python main.py backtest --strategy ma_cross --symbols BTCUSDT ETHUSDT

# 開始交易
python main.py trade --strategy ma_cross

# Web 介面
python main.py api

# 監控
python monitor.py
```

## 策略選擇建議

### 🔰 新手推薦
**移動平均交叉 (ma_cross)**
- 簡單易懂
- 風險相對較低
- 適合趨勢市場

### 🔄 進階策略
**RSI 策略**
- 適合震盪市場
- 需要較多經驗

**組合策略 (combined)**
- 結合多個指標
- 較為穩定但交易頻率較低

## 風險提醒

⚠️ **重要安全提示**
1. **永遠先在測試網測試**
2. **從小資金開始**
3. **定期檢查交易狀況**
4. **不要投入超過可承受損失的資金**
5. **充分理解策略風險**

## 常見問題

### Q: API 連接失敗怎麼辦？
A: 檢查 API 密鑰是否正確，網路連接是否穩定。

### Q: 回測顯示虧損怎麼辦？
A: 不要用該策略進行實盤交易，嘗試調整參數或換用其他策略。

### Q: 如何停止交易？
A: 按 Ctrl+C 或通過 Web 介面點擊停止按鈕。

### Q: 如何修改交易參數？
A: 編輯 `.env` 文件中的相關參數，重啟機器人生效。

## 獲得幫助

- 📖 查看完整文檔：README.md
- 🐛 報告問題：提交 GitHub Issue
- 💬 社群討論：加入討論群組

---

**祝您交易順利！記住：謹慎交易，風險自擔。** 🚀
