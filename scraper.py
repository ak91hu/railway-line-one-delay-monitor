import requests
import pandas as pd
import datetime
import os
import sys

DATA_FILE = "data.csv"

RELATIONS = [
    ("Budapest-Kelenföld", "Tatabánya"),
    ("Budapest-Kelenföld", "Győr"),
    ("Budapest-Kelenföld", "Hegyeshalom")
]

def get_elvira_data():
    new_rows = []
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    today_str = datetime.datetime.now().strftime("%y.%m.%d")
    
    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Referer": "http://elvira.mav-start.hu/"
    })

    for start_stat, end_stat in RELATIONS:
        try:
            url = f"http://elvira.mav-start.hu/elvira.dll/x/index?i={start_stat}&e={end_stat}&d={today_str}"
            response = session.get(url, timeout=20)
            
            if response.status_code == 200:
                dfs = pd.read_html(response.content, match="Indul", header=0)
                
                if len(dfs) > 0:
                    df = dfs[0]
                    
                    required_cols = [c for c in df.columns if "Vonat" in str(c)]
                    if not required_cols:
                        continue
                        
                    for _, row in df.iterrows():
                        try:
                            train_raw = str(row.get("Vonat", ""))
                            if pd.isna(train_raw) or len(train_raw) < 2:
                                continue
                                
                            train_id = train_raw.split("[")[0].strip()
                            
                            delay = 0
                            row_str = str(row.values)
                            if "+" in row_str:
                                import re
                                delays = re.findall(r'\+\s?(\d+)', row_str)
                                if delays:
                                    delay = int(max([int(d) for d in delays]))
                            
                            new_rows.append({
                                "timestamp": timestamp,
                                "relation": f"{start_stat} -> {end_stat}",
                                "train_id": train_id,
                                "destination": end_stat,
                                "delay": delay
                            })
                        except:
                            continue
        except:
            continue

    return pd.DataFrame(new_rows)

if __name__ == "__main__":
    df_new = get_elvira_data()
    
    if not df_new.empty:
        header = not os.path.exists(DATA_FILE)
        df_new.to_csv(DATA_FILE, mode='a', header=header, index=False)
    else:
        sys.exit(0)
