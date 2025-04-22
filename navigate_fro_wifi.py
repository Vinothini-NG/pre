import subprocess
import re
import sqlite3
import pandas as pd
import joblib
from collections import deque

# Load trained model
clf = joblib.load("zone_predictor_rf_model.joblib")

zone_graph = {
    "reception": ["hallway"],
    "hallway": ["reception", "cabin", "conference", "ec"],
    "cabin": ["hallway"],
    "conference": ["hallway"],
    "ec": ["hallway"]  # 👈 Add this!
}


# Scan Wi-Fi networks
def scan_wifi():
    command = "netsh wlan show networks mode=bssid"
    result = subprocess.check_output(command, shell=True, encoding='utf-8', errors='ignore')

    bssids = re.findall(r'BSSID\s+\d+\s*:\s*([\w:]+)', result)
    signals = re.findall(r'Signal\s*:\s*(\d+)%', result)

    wifi_data = []
    for bssid, signal in zip(bssids, signals):
        rssi = int(signal) // 2 - 100  # Convert % to approximate dBm
        wifi_data.append((bssid, rssi))

    return dict(wifi_data)
# Predict current zone using trained model
def predict_zone(wifi_dict):
    all_bssids = clf.feature_names_in_
    row = {bssid: wifi_dict.get(bssid, -100) for bssid in all_bssids}
    df = pd.DataFrame([row])
    predicted_zone = clf.predict(df)[0]
    return predicted_zone

# Find shortest path using BFS
def find_shortest_path(graph, start, goal):
    visited = set()
    queue = deque([[start]])

    if start == goal:
        return [start]

    while queue:
        path = queue.popleft()
        zone = path[-1]

        if zone not in visited:
            for neighbor in graph.get(zone, []):
                new_path = path + [neighbor]
                queue.append(new_path)
                if neighbor == goal:
                    return new_path
            visited.add(zone)
    return None

# Print directions
def print_instructions(path):
    print("\n🧭 Navigation Instructions:\n")
    for i in range(len(path) - 1):
        print(f"  → From '{path[i]}' go to '{path[i+1]}'")
    print("\n✅ You have reached your destination!\n")

# Main workflow
def navigate():
    print("📡 Scanning Wi-Fi to detect current location...")
    wifi_dict = scan_wifi()

    if not wifi_dict:
        print("❌ No Wi-Fi data found. Try again.")
        return

    current_zone = predict_zone(wifi_dict)
    print(f"📍 Detected current zone: {current_zone}")

    destination = input("🏁 Enter destination zone: ").strip().lower()

    if destination not in zone_graph:
        print("❌ Destination not found in zone graph.")
        return

    path = find_shortest_path(zone_graph, current_zone, destination)
    if path:
        print_instructions(path)
    else:
        print("❌ No path found between current and destination zones.")

if __name__ == "__main__":
    navigate()
