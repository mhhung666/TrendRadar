# TrendRadar × Cherry Studio 部署指南 🍒

> **適合人羣**：零編程基礎的用戶
> **客戶端**：Cherry Studio（免費開源 GUI 客戶端）

---

## 📥 第一步：下載 Cherry Studio

### Windows 用戶

訪問官網下載：https://cherry-ai.com/
或直接下載：[Cherry-Studio-Windows.exe](https://github.com/kangfenmao/cherry-studio/releases/latest)

### Mac 用戶

訪問官網下載：https://cherry-ai.com/
或直接下載：[Cherry-Studio-Mac.dmg](https://github.com/kangfenmao/cherry-studio/releases/latest)


---

## 📦 第二步：獲取項目代碼

爲什麼需要獲取項目代碼？

AI 分析功能需要讀取項目中的新聞數據才能工作。無論你使用 GitHub Actions 還是 Docker 部署，爬蟲生成的新聞數據都保存在項目的 output 目錄中。因此，在配置 MCP 服務器之前，需要先獲取完整的項目代碼（包含數據文件）。

根據你的技術水平，可以選擇以下任一方式獲取：：

### 方法一：Git Clone（推薦給技術用戶）

如果你熟悉 Git，可以使用以下命令克隆項目：

```bash
git clone https://github.com/你的用戶名/你的項目名.git
cd 你的項目名
```

**優點**：

- 可以隨時拉取一個命令就可以更新最新數據到本地了（`git pull`）

### 方法二：直接下載 ZIP 壓縮包（推薦給初學者）


1. **訪問 GitHub 項目頁面**

   - 項目鏈接：`https://github.com/你的用戶名/你的項目名`

2. **下載壓縮包**

   - 點擊綠色的 "Code" 按鈕
   - 選擇 "Download ZIP"
   - 或直接訪問：`https://github.com/你的用戶名/你的項目名/archive/refs/heads/master.zip`


**注意事項**：

- 步驟稍微麻煩，後續更新數據需要重複上面步驟，然後覆蓋本地數據(output 目錄)

---

## 🚀 第三步：一鍵部署 MCP 服務器

### Windows 用戶

1. **雙擊運行**項目文件夾中的 `setup-windows.bat`，如果有問題，就運行 `setup-windows-en.bat`
2. **等待安裝完成**
3. **記錄顯示的配置信息**（命令路徑和參數）

### Mac 用戶

1. **打開終端**（在啓動臺搜索"終端"）
2. **拖拽**項目文件夾中的 `setup-mac.sh` 到終端窗口
3. **按回車鍵**
4. **記錄顯示的配置信息**

---

## 🔧 第四步：配置 Cherry Studio

### 1. 打開設置

啓動 Cherry Studio，點擊右上角 ⚙️ **設置** 按鈕

### 2. 添加 MCP 服務器

在設置頁面找到：**MCP** → 點擊 **添加**

### 3. 填寫配置（重要！）

根據剛纔的安裝腳本顯示的信息填寫

### 4. 保存並啓用

- 點擊 **保存** 按鈕
- 確保 MCP 服務器列表中的開關是 **開啓** 狀態 ✅

---

## ✅ 第五步：驗證是否成功

### 1. 測試連接

在 Cherry Studio 的對話框中輸入：

```
幫我爬取最新的新聞
```

或者嘗試其他測試命令：

```
搜索最近3天關於"人工智能"的新聞
查找2025年1月的"特斯拉"相關報道
分析"iPhone"的熱度趨勢
```

**提示**：當你說"最近3天"時，AI會自動計算日期範圍並搜索。

### 2. 成功標誌

如果配置成功，AI 會：

- ✅ 調用 TrendRadar 工具
- ✅ 返回真實的新聞數據
- ✅ 顯示平臺、標題、排名等信息


---

## 🎯 進階配置

### HTTP 模式（可選）

如果需要遠程訪問或多客戶端共享，可以使用 HTTP 模式：

#### Windows

雙擊運行 `start-http.bat`

#### Mac

```bash
./start-http.sh
```

然後在 Cherry Studio 中配置：

```
類型: streamableHttp
URL: http://localhost:3333/mcp
```
