import requests
import pandas as pd
import datetime
import os
import time

DATA_FILE = "data.csv"

STATIONS = {
    "Budapest-Déli": "005501008",
    "Budapest-Kelenföld": "005501016",
    "Bicske": "005501198",
    "Tatabánya": "005501222",
    "Tata": "005501230",
    "Komárom": "005501248",
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
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }

    for station_name, station_id in STATIONS.items():
        try:
            url = "https://jegy.mav.hu/api/v1/komplex-search/station-scheduler"
            payload = {
                "stationId": station_id,
                "date": datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
                "direction": "DEPARTURE", 
                "trainFilter": "ALL_TRAINS"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "scheduler" in data:
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
            time.sleep(1)
            
        except Exception:
            pass

    return pd.DataFrame(new_rows)

if __name__ == "__main__":
    df_new = get_mav_data()
    
    if not df_new.empty:
        header = not os.path.exists(DATA_FILE)
        df_new.to_csv(DATA_FILE, mode='a', header=header, index=False)
