import sqlite3
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
import joblib

# Connect to the DB
conn = sqlite3.connect("zone_fingerprints.db")
cursor = conn.cursor()

# Load data
df = pd.read_sql_query("SELECT bssid, rssi, zone FROM fingerprints", conn)
conn.close()

# Pivot data: rows = samples, columns = BSSIDs, values = RSSI
pivoted = df.pivot_table(index=df.groupby(['zone']).cumcount(), 
                         columns='bssid', 
                         values='rssi').fillna(-100)  # Missing BSSIDs get -100

# Add zone labels
pivoted['zone'] = df['zone'].groupby(df.groupby(['zone']).cumcount()).first().values

# Separate features and target
X = pivoted.drop(columns='zone')
y = pivoted['zone']

# Train/test split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train model
clf = RandomForestClassifier(n_estimators=100, random_state=42)
clf.fit(X_train, y_train)

# Evaluate
y_pred = clf.predict(X_test)
print("\n📊 Classification Report:\n")
print(classification_report(y_test, y_pred))

# Save model
joblib.dump(clf, "zone_predictor_rf_model.joblib")
print("\n✅ Model saved as 'zone_predictor_rf_model.joblib'")
