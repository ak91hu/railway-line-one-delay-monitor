import requests
import pandas as pd
import datetime
import os
import random
import time

DATA_FILE = "data.csv"

LINE_1_KEYWORDS = [
    "Budaörs", "Biatorbágy", "Bicske", "Tatabánya", "Tata", "Komárom", "Ács", 
    "Győr", "Mosonmagyaróvár", "Hegyeshalom", "Rajka",
    "Oroszlány", "Sopron", "Szombathely",
    "Wien", "Bécs", "München", "Zürich", "Graz", "Salzburg", "Bratislava", "Pozsony"
]

def get_proxies():
    try:
        url = "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            return r.text.strip().split('\n')
    except:
        pass
    return []

def get_map_data_with_proxy():
    target_url = "http://vonatinfo.mav-start.hu/map.aspx/getData"
    
    payload = {
        "a": "TRAINS",
        "d": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "history": False,
        "id": False
    }
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    
    proxy_list = get_proxies()
    random.shuffle(proxy_list)
    
    if not proxy_list:
        proxy_list = [None]

    max_tries = 50
    for i, proxy in enumerate(proxy_list[:max_tries]):
        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        print(f"[{i+1}/{max_tries}] {proxy if proxy else 'Direct'} ... ", end="")
        
        try:
            response = requests.post(target_url, json=payload, headers=headers, proxies=proxy_dict, timeout=6)
            
            if response.status_code == 200:
                print("OK")
                return process_response(response)
            elif response.status_code == 403:
                print("403")
            else:
                print(response.status_code)
                
        except Exception:
            print("Hiba")
            
    return pd.DataFrame()

def process_response(response):
    try:
        data = response.json()
        if "d" in data and "result" in data["d"]:
            trains = data["d"]["result"]["Trains"]["Train"]
            new_rows = []
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
            
            for t in trains:
                relation = t.get("@Relation", "")
                if "Budapest" in relation and any(k in relation for k in LINE_1_KEYWORDS):
                    delay = int(t.get("@Delay", 0))
                    if delay < 0: delay = 0
                    
                    new_rows.append({
                        "timestamp": timestamp,
                        "train_id": t.get("@TrainNumber", "Ismeretlen"),
                        "relation": relation,
                        "delay": delay,
                        "lat": t.get("@Lat"),
                        "lon": t.get("@Lon")
                    })
            return pd.DataFrame(new_rows)
    except:
        pass
    return pd.DataFrame()

if __name__ == "__main__":
    df_new = get_map_data_with_proxy()
    
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            f.write("timestamp,train_id,relation,delay,lat,lon\n")
            
    if not df_new.empty:
        df_new.to_csv(DATA_FILE, mode='a', header=False, index=False)
        print(f"Mentve: {len(df_new)} sor")
    else:
        print("Nincs menthető adat")
