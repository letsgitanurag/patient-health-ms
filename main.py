from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel
import json
from pathlib import Path as FilePath
from ml_utils import save_patient

app = FastAPI()

BASE_DIR = FilePath(__file__).resolve().parent
DATA_FILE = BASE_DIR / "patients.json"

def file_loader():
    if not DATA_FILE.exists():
        return {}
    with open(DATA_FILE, "r") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError:
            return {}
    return data


@app.get("/")
def hello():
    return {"Message": "Patient management system API"}


@app.get("/about")
def about():
    return {"Message": "A fully functional API to manage patients records"}


@app.get("/view")
def view():
    data = file_loader()
    return data


@app.get("/patient/{patient_id}")
def view_patient(patient_id : str = Path(..., description = 'The Id of the patient in DB', examples = ['P001'])):
    data = file_loader()

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code= 404, detail = 'This Patient does not Exist')


@app.get('/sort')
def sort_patients(sort_by: str = Query(..., description= 'Sort the value on the basis of height, weight and Bmi'), order: str = Query('asc', description= 'Change the order of Data')):

    Valid_fields = ['height', 'weight', 'bmi']

    if sort_by not in Valid_fields:
        raise HTTPException(status_code= 400, detail = f'Invalid value only select from {Valid_fields}')
    if order not in ['asc', 'desc']:
        raise HTTPException(status_code= 400, detail= 'Invalid order only select between asc and desc')

    data = file_loader()

    sort_order = True if order== 'desc' else False

    sorted_Data = sorted(data.values(), key = lambda x: x.get(sort_by, 0), reverse = sort_order)

    return sorted_Data

class PatientModel(BaseModel):
    name: str
    age: int
    gender: str
    height: float
    weight: float
    bmi: float
    verdict: str
    city: str = "Unknown"

@app.post("/patient")
def create_patient(patient: PatientModel):
    try:
        new_id = save_patient(
            patient.name, patient.age, patient.gender, 
            patient.height, patient.weight, patient.bmi, 
            patient.verdict, patient.city
        )
        return {"message": "Patient added successfully", "patient_id": new_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))