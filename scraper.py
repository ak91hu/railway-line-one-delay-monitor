import requests
import pandas as pd
import datetime
import os
import random
import time
import json

DATA_FILE = "data.csv"

LINE_1_KEYWORDS = [
    "Budaörs", "Biatorbágy", "Bicske", "Tatabánya", "Tata", "Komárom", "Ács", 
    "Győr", "Mosonmagyaróvár", "Hegyeshalom", "Rajka",
    "Oroszlány", "Sopron", "Szombathely",
    "Wien", "Bécs", "München", "Zürich", "Graz", "Salzburg", "Bratislava", "Pozsony"
]

def get_proxies():
    print("Proxy lista letöltése...")
    sources = [
        "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
        "https://raw.githubusercontent.com/monosans/proxy-list/main/proxies/http.txt", 
        "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt"
    ]
    collected = set()
    for url in sources:
        try:
            r = requests.get(url, timeout=5)
            if r.status_code == 200:
                lines = r.text.strip().split('\n')
                for line in lines:
                    if line.strip(): collected.add(line.strip())
        except: pass
    return list(collected)

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
    if not proxy_list: proxy_list = [None]
    
    print(f"Összesen {len(proxy_list)} proxy van a listán.")

    max_tries = 5000
    
    for i, proxy in enumerate(proxy_list[:max_tries]):
        proxy_dict = {"http": f"http://{proxy}", "https": f"http://{proxy}"} if proxy else None
        print(f"[{i+1}/{max_tries}] {proxy if proxy else 'Direct'} ... ", end="")
        
        try:
            response = requests.post(target_url, json=payload, headers=headers, proxies=proxy_dict, timeout=5)
            
            if response.status_code == 200:
                # KRITIKUS RÉSZ: Ellenőrizzük, hogy TÉNYLEG adat jött-e, vagy csak egy HTML oldal
                try:
                    data = response.json()
                    # Ellenőrizzük a MÁV struktúrát
                    if "d" in data and "result" in data["d"]:
                        print("OK (Valid JSON) ✅")
                        return process_response(data)
                    else:
                        print("Fals 200 (Rossz JSON struktúra) ⚠️ -> Tovább")
                except json.JSONDecodeError:
                    print(f"Fals 200 (HTML szemét jött: {response.text[:20].replace(chr(10), '')}...) ⚠️ -> Tovább")
            
            elif response.status_code == 403:
                print("403 (Tiltva)")
            else:
                print(response.status_code)
                
        except Exception:
            print("Timeout/Hiba")
            
    return pd.DataFrame()

def process_response(data):
    try:
        trains = data["d"]["result"]["Trains"]["Train"]
        print(f"    -> Teljes vonatlista letöltve: {len(trains)} db vonat az országban.")
        
        new_rows = []
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
        
        for t in trains:
            relation = t.get("@Relation", "")
            # Lazítottam a szűrésen: Elég ha a Kulcsszó benne van, nem kell a 'Budapest' kötelezően
            # Mert van olyan, hogy 'Hegyeshalom - Wien' (nincs benne Pest)
            if any(k in relation for k in LINE_1_KEYWORDS):
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
        
        print(f"    -> Ebből releváns (1-es vonal): {len(new_rows)} db")
        return pd.DataFrame(new_rows)
    except Exception as e:
        print(f"    -> Feldolgozási hiba: {e}")
        pass
    return pd.DataFrame()

if __name__ == "__main__":
    df_new = get_map_data_with_proxy()
    
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w') as f:
            f.write("timestamp,train_id,relation,delay,lat,lon\n")
            
    if not df_new.empty:
        df_new.to_csv(DATA_FILE, mode='a', header=False, index=False)
        print(f"SIKER: {len(df_new)} sor mentve!")
    else:
        print("HIBA: Nincs menthető adat (vagy minden proxy rossz volt).")
        # Exit code hiba, hogy a GitHub Action piros legyen, ha nem sikerült
        import sys
        if len(get_proxies()) > 0: # Csak akkor hiba, ha volt miből próbálkozni
             sys.exit(1)
