import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import LabelEncoder
import joblib
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_FILE = BASE_DIR / "patients.json"
MODEL_FILE = BASE_DIR / "model.pkl"

def load_data():
    if not DATA_FILE.exists():
        return pd.DataFrame(columns=['name', 'city', 'age', 'gender', 'height', 'weight', 'bmi', 'verdict'])

    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
             return pd.DataFrame(columns=['name', 'city', 'age', 'gender', 'height', 'weight', 'bmi', 'verdict'])
    
    # Convert dictionary to DataFrame
    df = pd.DataFrame.from_dict(data, orient='index')
    return df

def save_patient(name, age, gender, height, weight, bmi, verdict, city="Unknown"):
    if DATA_FILE.exists():
        with open(DATA_FILE, "r") as f:
            try:
                data = json.load(f)
            except json.JSONDecodeError:
                data = {}
    else:
        data = {}
        
    # Generate ID
    new_id = f"P{len(data) + 1:03d}"
    
    data[new_id] = {
        "name": name,
        "city": city,
        "age": age,
        "gender": gender,
        "height": height,
        "weight": weight,
        "bmi": bmi,
        "verdict": verdict
    }
    
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)
        
    return new_id

def train_model():
    df = load_data()
    
    if df.empty:
        print("No data to train on.")
        return
    
    # Preprocessing
    gender_map = {'male': 0, 'female': 1}
    df['gender_encoded'] = df['gender'].map(gender_map)
    # Handle NaNs if any invalid gender
    df['gender_encoded'] = df['gender_encoded'].fillna(0)
    
    X = df[['age', 'gender_encoded', 'height', 'weight', 'bmi']]
    y = df['verdict']
    
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    model.fit(X, y)
    
    # Save model only
    joblib.dump(model, MODEL_FILE)
    print("Model trained and saved.")

def predict_verdict(age, gender, height, weight, bmi):
    if not MODEL_FILE.exists():
        train_model()
    
    try:
        model = joblib.load(MODEL_FILE)
    except Exception:
        # If loading fails (e.g. old format), retrain
        train_model()
        model = joblib.load(MODEL_FILE)

    gender_map = {'male': 0, 'female': 1}
    gender_encoded = gender_map.get(gender.lower(), 0)
    
    prediction = model.predict([[age, gender_encoded, height, weight, bmi]])
    return prediction[0]

if __name__ == "__main__":
    train_model()
