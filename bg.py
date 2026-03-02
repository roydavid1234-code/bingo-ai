import json
import os
import re
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

DB_FILE = "history.json"
MAX_HISTORY = 10

def fetch_bingo_now():
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("window-size=1920,1080")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36")
    
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)
    url = "https://lotto.auzonet.com/bingobingoV1.php"
    
    try:
        print(f"🚀 啟動強化快照模式，前往：{url}")
        driver.get(url)
        
        # 增加等待時間，確保所有 CSS 樣式與號碼球完整渲染
        print("⏳ 正在等待 12 秒讓開獎結果完全加載...")
        time.sleep(12)
        
        html_snapshot = driver.page_source
        driver.quit()
        
        soup = BeautifulSoup(html_snapshot, "html.parser")
        new_records = []
        
        # 優先找尋奧索特定的資料行類別
        rows = soup.find_all("tr", class_=re.compile(r"list_tr|list_tr2"))
        if not rows:
            rows = soup.find_all("tr") # 備用方案：抓取所有行

        for row in rows:
            if len(new_records) >= MAX_HISTORY:
                break
            
            cols = row.find_all("td")
            if len(cols) < 2:
                continue
            
            # 1. 提取期數 (cols[0])
            period_text = cols[0].get_text(" ", strip=True)
            period_match = re.search(r'(\d{9,10})', period_text)
            if not period_match:
                continue
            period = period_match.group(1)

            # 2. 提取號碼 (cols[1]) - 使用雙軌偵測
            cell_html = str(cols[1])
            
            # 軌道 A：不分大小寫尋找 nBXX 格式 (最準確，可避開序號)
            found_nums = re.findall(r'[nN][bB](\d{2})', cell_html)
            
            # 軌道 B：如果類別抓不到，抓取所有 01-80 數字並排除前 20 個可能是序號的數字
            if len(set(found_nums)) < 20:
                all_possible = re.findall(r'\b([0-7][0-9]|80)\b', cols[1].get_text(" ", strip=True))
                if len(all_possible) >= 40: # 如果包含序號，通常會有 40 個數字 (20序號+20號碼)
                    # 奧索結構中，序號通常在前或在後，這裡我們取「非連續增量」的那一組
                    found_nums = all_possible[20:] if all_possible[0] == "01" else all_possible[:20]
                else:
                    found_nums = all_possible

            # 整理號碼：去重、排序、取前 20 個
            unique_nums = sorted(list(set(found_nums)))
            
            if len(unique_nums) >= 20:
                final_nums = unique_nums[:20]
                new_records.append({
                    "period": period,
                    "numbers": final_nums
                })
                print(f"✅ 成功擷取正確數據！期數 {period}: {' '.join(final_nums)}")

        if not new_records:
            print("❌ 解析失敗：找不到符合格式的數據。")
            return None
            
        with open(DB_FILE, 'w', encoding='utf-8') as f:
            json.dump(new_records, f, ensure_ascii=False, indent=2)
        print(f"💾 任務完成：已儲存前 {len(new_records)} 期數據。")
        return new_records[0]

    except Exception as e:
        print(f"⚠️ 發生錯誤: {e}")
        return None

if __name__ == "__main__":
    fetch_bingo_now()