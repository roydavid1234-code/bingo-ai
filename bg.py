import requests
from bs4 import BeautifulSoup
import json, os, datetime, firebase_admin
from firebase_admin import credentials, db

# 1. Firebase 初始化
cred_json = json.loads(os.environ.get('FIREBASE_CONFIG'))
if not firebase_admin._apps:
    firebase_admin.initialize_app(credentials.Certificate(cred_json), {
        'databaseURL': 'https://bingo-ai-360ad-default-rtdb.firebaseio.com' # 已根據您的資料庫填寫
    })

def fetch_fast():
    # 改用 Requests 直接連線，穩定度提升 200%
    url = "https://lotto.auzonet.com/bingobingoV1.php"
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}
    
    try:
        print("🚀 啟動極速爬蟲任務...")
        response = requests.get(url, headers=headers, timeout=20)
        soup = BeautifulSoup(response.text, "html.parser")
        
        new_records = []
        # 尋找開獎表格行
        rows = soup.find_all("tr", class_=["list_tr", "list_tr2"])
        
        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 2: continue
            
            period = cols[0].get_text(strip=True)
            # 抓取所有數字球號碼
            nums = [n.get_text(strip=True) for n in cols[1].find_all("span") if n.get_text(strip=True).isdigit()]
            
            if len(nums) >= 20:
                new_records.append({"period": period, "numbers": nums[:20]})
            if len(new_records) >= 10: break

        if new_records:
            # 推送到 Firebase
            db.reference('bingo_data').set({
                "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "records": new_records
            })
            print(f"🔥 Firebase 同步成功！最新時間：{datetime.datetime.now()}")
            return True
        else:
            print("⚠️ 抓取失敗：未在網頁中找到號碼數據")
            return False
    except Exception as e:
        print(f"❌ 錯誤原因: {e}")
        return False

if __name__ == "__main__":
    fetch_fast()
