import requests
import pandas as pd
import datetime
import os
import time
import sys

DATA_FILE = "data.csv"

# Állomás ID-k
STATIONS = {
    "Budapest-Kelenföld": "005501016",
    "Tatabánya": "005501222",
    "Győr": "005501289"
}

# Célállomás szűrő (Ha a vonat célállomása tartalmazza ezek egyikét)
LINE_1_TARGETS = [
    "Győr", "Hegyeshalom", "Rajka", "Oroszlány", 
    "Wien", "München", "Zürich", "Graz", "Sopron", "Szombathely"
]

def get_mav_data():
    new_rows = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"--- INDÍTÁS: {timestamp} ---")
    print(f"Python version: {sys.version}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }

    found_any_train = False

    for station_name, station_id in STATIONS.items():
        print(f"\nLekérdezés: {station_name} ({station_id})...")
        try:
            url = "https://jegy.mav.hu/api/v1/komplex-search/station-scheduler"
            payload = {
                "stationId": station_id,
                "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "direction": "DEPARTURE", 
                "trainFilter": "ALL_TRAINS"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            print(f"STATUS CODE: {response.status_code}")
            
            if response.status_code != 200:
                print(f"HIBA! A szerver válasza: {response.text[:200]}")
                continue

            data = response.json()
            
            if "scheduler" in data:
                trains = data["scheduler"]
                print(f"-> Talált vonatok száma: {len(trains)}")
                found_any_train = True
                
                for t in trains:
                    dest = t.get("destination", {}).get("name", "")
                    
                    # DEBUG: Írjuk ki, mit vizsgálunk
                    # print(f"   Vizsgálat: {dest}") 
                    
                    # Szűrés ellenőrzése
                    if any(target in dest for target in LINE_1_TARGETS):
                        kind = t.get("trainKind", {}).get("sort", "")
                        number = t.get("trainNumber", "")
                        full_id = f"{kind} {number}"
                        delay = t.get("diff", 0)
                        
                        print(f"   [OK] Hozzáadva: {full_id} -> {dest} (Késés: {delay} perc)")
                        
                        new_rows.append({
                            "timestamp": timestamp,
                            "station": station_name,
                            "train_id": full_id,
                            "destination": dest,
                            "delay": delay
                        })
                    # else:
                        # print(f"   [SKIP] Nem 1-es vonal: {dest}")

            else:
                print("-> Üres válasz (nincs 'scheduler' kulcs).")

            time.sleep(1)
            
        except Exception as e:
            print(f"!!! KRITIKUS HIBA ({station_name}): {e}")

    if not found_any_train:
        print("\nFIGYELEM: Egyetlen állomáson sem találtunk vonatlistát!")

    return pd.DataFrame(new_rows)

if __name__ == "__main__":
    df_new = get_mav_data()
    
    print(f"\n--- ÖSSZESÍTÉS ---")
    print(f"Mentésre váró sorok száma: {len(df_new)}")
    
    if not df_new.empty:
        # Mindig létrehozzuk/hozzáfűzzük
        header = not os.path.exists(DATA_FILE)
        df_new.to_csv(DATA_FILE, mode='a', header=header, index=False)
        print(f"SIKER: data.csv frissítve/létrehozva.")
        
        # DEBUG: Ellenőrzés, hogy a fájl tényleg ott van-e
        if os.path.exists(DATA_FILE):
            print(f"Fájlméret: {os.path.getsize(DATA_FILE)} byte")
    else:
        print("Nincs mit menteni. A data.csv NEM jön létre/frissül.")
        # KILÉPÉSI KÓD HIBA, HOGY A GITHUB ACTION ÉSZREVEGYE!
        # Ha ezt a sort benne hagyod, "piros" lesz a build, ha nincs vonat.
        # De legalább látod a logban.
        exit(1)
