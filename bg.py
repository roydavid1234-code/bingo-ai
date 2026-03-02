import requests
from bs4 import BeautifulSoup
import json, os, datetime, firebase_admin
from firebase_admin import credentials, db

# Firebase 初始化 (保持不變)
cred_json = json.loads(os.environ.get('FIREBASE_CONFIG'))
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_json), {
        'databaseURL': 'https://bingo-ai-360ad-default-rtdb.firebaseio.com'
    })

def fetch_fast():
    # 改用直接請求，不需要啟動 Chrome
    url = "https://lotto.auzonet.com/bingobingoV1.php"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win14; x64) AppleWebKit/537.36'}
    
    try:
        print("🚀 啟動極速爬蟲 (Requests 模式)...")
        response = requests.get(url, headers=headers, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        
        new_records = []
        # 尋找所有包含號碼的表格行
        rows = soup.find_all("tr", class_=["list_tr", "list_tr2"])
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2: continue
            
            period = cols[0].get_text(strip=True)
            # 抓取所有藍色號碼球 (class="nBXX")
            nums = [n.get_text(strip=True) for n in cols[1].find_all("span") if n.get_text(strip=True).isdigit()]
            
            if len(nums) >= 20:
                new_records.append({"period": period, "numbers": nums[:20]})
            if len(new_records) >= 10: break

        if new_records:
            db.reference('bingo_data').set({
                "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "records": new_records
            })
            print(f"🔥 即時同步成功！時間：{datetime.datetime.now()}")
            return True
        return False
    except Exception as e:
        print(f"❌ 抓取失敗: {e}")
        return False

if __name__ == "__main__":
    fetch_fast()
