import pandas as pd
import datetime
import os
import time
from curl_cffi import requests

DATA_FILE = "data.csv"

STATIONS = {
    "Budapest-Kelenföld": "005501016",
    "Tatabánya": "005501222",
    "Győr": "005501289",
    "Mosonmagyaróvár": "005501305",
    "Hegyeshalom": "005501313"
}

LINE_1_TARGETS = [
    "Győr", "Hegyeshalom", "Rajka", "Oroszlány", 
    "Wien", "München", "Zürich", "Graz", "Sopron", "Szombathely"
]

def get_mav_data():
    new_rows = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    
    print(f"--- INDÍTÁS: {timestamp} ---")

    for station_name, station_id in STATIONS.items():
        print(f"Lekérdezés: {station_name} ...", end="")
        
        try:
            url = "https://jegy.mav.hu/api/v1/komplex-search/station-scheduler"
            
            payload = {
                "stationId": station_id,
                "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "direction": "DEPARTURE", 
                "trainFilter": "ALL_TRAINS"
            }
            
            response = requests.post(
                url, 
                json=payload, 
                impersonate="chrome120", 
                timeout=20
            )
            
            if response.status_code == 200:
                data = response.json()
                if "scheduler" in data:
                    count = 0
                    for t in data["scheduler"]:
                        dest = t.get("destination", {}).get("name", "")
                        
                        if any(target in dest for target in LINE_1_TARGETS):
                            kind = t.get("trainKind", {}).get("sort", "")
                            number = t.get("trainNumber", "")
                            full_id = f"{kind} {number}"
                            delay = t.get("diff", 0)
                            
                            new_rows.append({
                                "timestamp": timestamp,
                                "station": station_name,
                                "train_id": full_id,
                                "destination": dest,
                                "delay": delay
                            })
                            count += 1
                    print(f" SIKER! ({count} vonat)")
                else:
                    print(" Üres válasz.")
            else:
                print(f" Hiba kód: {response.status_code}")
                
            time.sleep(2)
            
        except Exception as e:
            print(f" Hiba: {e}")

    return pd.DataFrame(new_rows)

if __name__ == "__main__":
    df_new = get_mav_data()
    
    if not df_new.empty:
        header = not os.path.exists(DATA_FILE)
        df_new.to_csv(DATA_FILE, mode='a', header=header, index=False)
        print(f"MENTVE: {len(df_new)} sor.")
    else:
        print("Nincs új adat.")
