import requests
import pandas as pd
import datetime
import os
import json
import time

DATA_FILE = "data.csv"

LINE_1_KEYWORDS = [
    "Győr", "Hegyeshalom", "Wien", "München", "Zürich", 
    "Graz", "Sopron", "Szombathely", "Tatabánya", "Komárom", "Rajka"
]

def get_tamas_method_data():
    print("--- MÁV 'Map' API Lekérdezés (Ferenci-módszer) ---")
    url = "http://vonatinfo.mav-start.hu/map.aspx/getData"
    
    payload = {
        "a": "TRAINS",
        "d": datetime.datetime.now().strftime("%Y%m%d%H%M%S"),
        "history": False,
        "id": False
    }
    
    headers = {
        "Content-Type": "application/json; charset=UTF-8",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
        "Referer": "http://vonatinfo.mav-start.hu/"
    }
    
    try:
        print(f"Kérés küldése ide: {url}")
        # POST kérés küldése
        response = requests.post(url, json=payload, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Az adatstruktúra kibontása: d -> result -> Trains -> Train
            if "d" in data and "result" in data["d"] and "Trains" in data["d"]["result"]:
                trains_raw = data["d"]["result"]["Trains"]["Train"]
                
                print(f"Sikeres válasz! Összes vonat az országban: {len(trains_raw)}")
                
                new_rows = []
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
                
                for t in trains_raw:
                    # Adatmezők kinyerése (az ő rendszerükben @-al kezdődik)
                    relation = t.get("@Relation", "")
                    train_num = t.get("@TrainNumber", "")
                    
                    # SZŰRÉS: Csak az 1-es vonal érdekel minket
                    # Feltétel: Legyen benne "Budapest" ÉS valamelyik 1-es vonali város
                    if "Budapest" in relation and any(k in relation for k in LINE_1_KEYWORDS):
                        
                        delay = int(t.get("@Delay", 0))
                        if delay < 0: delay = 0 # Negatív késés (sietés) legyen 0
                        
                        new_rows.append({
                            "timestamp": timestamp,
                            "train_id": train_num,
                            "relation": relation,
                            "delay": delay,
                            "lat": t.get("@Lat"), # Koordináta (ha térképre tennéd)
                            "lon": t.get("@Lon")
                        })
                
                print(f"Ebből az 1-es vonalhoz tartozik: {len(new_rows)} db")
                return pd.DataFrame(new_rows)
            else:
                print("A JSON válasz nem tartalmaz 'Trains' listát.")
        else:
            print(f"Hiba: {response.status_code} (A szerver elutasította a kérést)")
            
    except Exception as e:
        print(f"Kritikus hiba: {e}")

    return pd.DataFrame()

if __name__ == "__main__":
    # 1. Adatok lekérése
    df_new = get_tamas_method_data()
    
    # 2. Mentés (Hibabiztos módon)
    # Ha a fájl nem létezik, létrehozzuk a fejlécet
    if not os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            f.write("timestamp,train_id,relation,delay,lat,lon\n")
            
    if not df_new.empty:
        # Hozzáfűzés
        df_new.to_csv(DATA_FILE, mode='a', header=False, index=False)
        print("Adatok sikeresen mentve a CSV-be.")
    else:
        print("Nincs új menthető adat.")
