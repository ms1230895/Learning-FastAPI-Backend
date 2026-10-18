from fastapi import FastAPI, Path, HTTPException, Query
import json

app = FastAPI()

def load_data():
    with open("patients.json", "r") as f:
        data =  json.load(f)
    return data

@app.get("/")
def read_root():
    return {"message": "Patient Management System API is running!"}

@app.get("/about")
def about():
    return {"message": "This API is designed to manage patient records, appointments, and related healthcare data."}

@app.get("/view")
def view_data():
    data = load_data()
    return data

@app.get("/patients/{patient_id}")
def view_patient(patient_id: str = Path(..., description="The ID of the patient to retrieve",example="P001")):
    data = load_data() #load all patients data

    if patient_id in data:
        return data[patient_id]
    raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found.")

@app.get("/sort")
def sort_patients(sorted_by: str = Query(..., description="sort on the basis of wieght,height or bmi"), order = Query("asc", description="Order of sorting: 'asc' for ascending, 'desc' for descending")):
    valid_sort_fields = ["weight", "height", "bmi"]
    if sorted_by not in valid_sort_fields:
        raise HTTPException(status_code=400, detail=f"Invalid sort field. Must be one of {valid_sort_fields}.")
    if order not in ["asc", "desc"]:
        raise HTTPException(status_code=400, detail=f"Invalid order. Must be 'asc' or 'desc'.")

    data = load_data()

    sort_order = False if order == "desc" else True

    sorted_data = sorted(data.items(), key=lambda x: x[1][sorted_by], reverse=sort_order)

    return sorted_data



    


