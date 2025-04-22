import subprocess
import sqlite3
import re
from datetime import datetime
from tabulate import tabulate

# Initialize SQLite DB
conn = sqlite3.connect("zone_fingerprints.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS fingerprints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    bssid TEXT,
    rssi INTEGER,
    zone TEXT,
    timestamp TEXT
)
""")
conn.commit()

def scan_wifi():
    command = "netsh wlan show networks mode=bssid"
    result = subprocess.check_output(command, shell=True, encoding='mbcs', errors='ignore')

    print("\n[DEBUG] Raw netsh output:\n", result)

    # More robust regex patterns
    bssids = re.findall(r'BSSID\s+\d+\s*:\s*([\w:]+)', result)
    signal_levels = re.findall(r'Signal\s*:\s*(\d+)%', result)

    print(f"[DEBUG] Parsed BSSIDs: {bssids}")
    print(f"[DEBUG] Parsed Signal Levels: {signal_levels}")

    wifi_data = []
    for bssid, signal in zip(bssids, signal_levels):
        rssi = int(signal) // 2 - 100  # Convert signal % to approx dBm
        wifi_data.append((bssid, rssi))
    
    return wifi_data



def save_fingerprints(wifi_data, zone):
    timestamp = datetime.now().isoformat()
    for bssid, rssi in wifi_data:
        cursor.execute("INSERT INTO fingerprints (bssid, rssi, zone, timestamp) VALUES (?, ?, ?, ?)",
                       (bssid, rssi, zone, timestamp))
    conn.commit()

def main():
    print("Zone-Based Wi-Fi Fingerprint Collector")
    while True:
        zone = input("Enter zone name (e.g., Room A, Entrance): ").strip()
        print(f"Scanning Wi-Fi for zone '{zone}'...")

        data = scan_wifi()
        if not data:
            print("No networks found.")
            continue

        print(tabulate(data, headers=["BSSID", "RSSI (dBm)"]))
        save = input("Save this fingerprint? (y/n): ").strip().lower()
        if save == 'y':
            save_fingerprints(data, zone)
            print("Saved!")
        
        cont = input("Scan another zone? (y/n): ").strip().lower()
        if cont != 'y':
            break

if __name__ == "__main__":
    main()
