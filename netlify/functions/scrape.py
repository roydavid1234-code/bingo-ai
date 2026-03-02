import requests
from bs4 import BeautifulSoup
import json, os, datetime, firebase_admin
from firebase_admin import credentials, db

def initialize_firebase():
    cred_json_str = os.environ.get('FIREBASE_CONFIG')
    if not cred_json_str:
        return False
    try:
        if not firebase_admin._apps:
            cred_dict = json.loads(cred_json_str)
            firebase_admin.initialize_app(credentials.Certificate(cred_dict), {
                'databaseURL': 'https://bingo-ai-360ad-default-rtdb.firebaseio.com' 
            })
        return True
    except:
        return False

def handler(event, context):
    if not initialize_firebase():
        return {"statusCode": 500, "body": json.dumps({"error": "Firebase Config Missing"})}

    try:
        # 爬蟲邏輯
        url = "https://lotto.auzonet.com/bingobingoV1.php"
        res = requests.get(url, headers={'User-Agent': 'Mozilla/5.0'}, timeout=15)
        soup = BeautifulSoup(res.text, "html.parser")
        
        new_records = []
        rows = soup.find_all("tr", class_=["list_tr", "list_tr2"])
        for row in rows[:5]: # 抓前5期
            cols = row.find_all("td")
            if len(cols) >= 2:
                period = cols[0].get_text(strip=True)
                nums = [n.get_text(strip=True) for n in cols[1].find_all("span") if n.get_text(strip=True).isdigit()]
                new_records.append({"period": period, "numbers": nums})

        # 同步到 Firebase
        db.reference('bingo_data').set({
            "last_update": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "records": new_records
        })

        return {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json", "Access-Control-Allow-Origin": "*"},
            "body": json.dumps({"status": "success", "period": new_records[0]['period']})
        }
    except Exception as e:
        return {"statusCode": 500, "body": json.dumps({"error": str(e)})}
