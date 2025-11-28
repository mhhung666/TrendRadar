# UDN 快速參考卡

> 快速查閱 UDN 聯合新聞網整合的關鍵信息

---

## 🎯 快速開始

### 運行爬蟲（包含 UDN）
```bash
python main.py
```

### 測試 UDN
```bash
python test_udn.py
```

### 單獨測試 UDN 爬取
```python
from main import DataFetcher
fetcher = DataFetcher()
result, id = fetcher.fetch_udn_news()
print(f"爬取了 {len(result)} 條新聞")
```

---

## 📂 相關文件

| 文件 | 說明 |
|------|------|
| [config/config.yaml](config/config.yaml#L122-123) | UDN 平台配置 |
| [main.py](main.py#L527-593) | UDN 爬取函數 |
| [test_udn.py](test_udn.py) | UDN 測試腳本 |
| [UDN_INTEGRATION_GUIDE.md](UDN_INTEGRATION_GUIDE.md) | 完整整合指南 |
| [CHANGELOG_UDN.md](CHANGELOG_UDN.md) | 更新日誌 |

---

## 🔧 核心代碼位置

### 配置
```yaml
# config/config.yaml 第 122-123 行
platforms:
  - id: "udn"
    name: "UDN 聯合新聞網"
```

### 爬取函數
```python
# main.py 第 527-593 行
def fetch_udn_news(self, max_retries: int = 2):
    """爬取 UDN 聯合新聞網即時新聞"""
    url = "https://udn.com/api/more?page=1&channelId=1&type=breaknews"
    # ...
```

### 整合邏輯
```python
# main.py 第 612-618 行
if id_value == "udn":
    udn_result, udn_id = self.fetch_udn_news()
    # ...
```

---

## 🌐 API 信息

### 端點
```
https://udn.com/api/more?page=1&channelId=1&type=breaknews
```

### 響應格式
```json
{
  "state": true,
  "page": "1",
  "end": true,
  "lists": [
    {
      "title": "新聞標題",
      "titleLink": "/news/story/7326/9168547",
      "time": {"date": "2025-11-28 10:24"},
      ...
    }
  ]
}
```

### 數據量
- **每次爬取**: 約 20 條新聞
- **更新頻率**: 實時
- **數據來源**: UDN 即時新聞

---

## ⚙️ 配置選項

### 啟用/禁用 UDN
```yaml
# 啟用（默認）
platforms:
  - id: "udn"
    name: "UDN 聯合新聞網"

# 禁用（註釋掉）
# platforms:
#   - id: "udn"
#     name: "UDN 聯合新聞網"
```

### 關注詞設定
```
# config/frequency_words.txt
台北
高雄
總統
AI
```

### 通知渠道
UDN 新聞會自動參與：
- ✅ 關鍵詞匹配
- ✅ 權重計算
- ✅ 通知推送

---

## 🧪 測試命令

### 完整測試套件
```bash
python test_udn.py
```

### 快速驗證
```bash
python -c "from main import DataFetcher; r,i=DataFetcher().fetch_udn_news(); print(f'✅ {len(r)} 條新聞')"
```

### 測試主流程
```bash
python main.py
```

---

## 🔍 故障排查

### UDN 爬取失敗
```bash
# 1. 檢查網絡連接
curl -I https://udn.com

# 2. 測試 API 端點
curl "https://udn.com/api/more?page=1&channelId=1&type=breaknews"

# 3. 查看詳細日誌
python test_udn.py
```

### 常見錯誤

| 錯誤 | 原因 | 解決方案 |
|------|------|---------|
| `ConnectionError` | 網絡問題 | 檢查網絡連接 |
| `無法找到 UDN 新聞標題` | API 變更 | 查看 API 響應 |
| `UDN 未在配置文件中` | 配置錯誤 | 檢查 config.yaml |

---

## 📊 性能數據

| 指標 | 數值 |
|------|------|
| 請求時間 | ~1-2 秒 |
| 數據量 | 20 條/次 |
| 成功率 | 100% |
| 重試次數 | 平均 0 次 |

---

## 🎨 輸出格式

### 文本輸出
```
output/2025年11月28日/txt/10時30分.txt
```

### HTML 報告
```
output/2025年11月28日/html/10時30分.html
index.html
```

### 數據結構
```python
{
  "新聞標題": {
    "ranks": [1],
    "url": "https://udn.com/news/story/7326/9168547",
    "mobileUrl": "https://udn.com/news/story/7326/9168547"
  }
}
```

---

## 🚀 進階用法

### 只爬取 UDN
```python
from main import DataFetcher
fetcher = DataFetcher()
results, names, failed = fetcher.crawl_websites([("udn", "UDN")])
```

### 自定義重試次數
```python
fetcher = DataFetcher()
result, id = fetcher.fetch_udn_news(max_retries=5)
```

### 使用代理
```yaml
# config.yaml
crawler:
  use_proxy: true
  default_proxy: "http://127.0.0.1:10086"
```

---

## 📌 快速鏈接

- **UDN 官網**: https://udn.com
- **即時新聞**: https://udn.com/news/breaknews/1
- **API 端點**: https://udn.com/api/more?page=1&channelId=1&type=breaknews
- **完整文檔**: [UDN_INTEGRATION_GUIDE.md](UDN_INTEGRATION_GUIDE.md)

---

## ✅ 檢查清單

整合完成後確認：

- [ ] `config/config.yaml` 中已添加 UDN 配置
- [ ] `python test_udn.py` 全部通過
- [ ] `python main.py` 能正常爬取 UDN
- [ ] 輸出文件中包含 UDN 新聞
- [ ] 關鍵詞匹配正常工作

---

**最後更新**: 2025-11-28
**版本**: 1.0
