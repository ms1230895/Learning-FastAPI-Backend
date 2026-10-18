from fastapi import FastAPI, Path, HTTPException, Query
from fastapi.responses import JSONResponse
from typing import Optional, Annotated, List, Literal
from pydantic import BaseModel, Field, computed_field, field_validator
import json

app = FastAPI()


class patient(BaseModel):

    id: Annotated[str, Field(..., description="Unique identifier for the patient", example="P001")]
    name:Annotated[str, Field(..., description="Name of the patient", example="John Doe")]
    city: Annotated[Optional[str], Field(default=None, description="City of the patient", example="Mumbai")]
    age: Annotated[int, Field(..., description="Age of the patient", example=30)]
    gender: Annotated[Literal['male', 'female', 'other'], Field(..., description="Gender of the patient", example="male")]
    height: Annotated[float, Field(..., description="Height of the patient in m", example=175.5)]
    weight: Annotated[float, Field(..., description="Weight of the patient in kg", example=70.2)]

    @field_validator('gender', mode='before')
    @classmethod
    def lowercase_gender(cls, value):
        # Accept "Male"/"male" alike, since patients.json stores lowercase
        return value.lower() if isinstance(value, str) else value

    @computed_field
    @property
    def bmi(self) -> float:
        if self.height > 0:
            bmi_value = self.weight / (self.height ** 2)
            return bmi_value

    @computed_field
    @property
    def verdict(self) -> str:
        if self.bmi < 18.5:
            return "Underweight"
        elif 18.5 <= self.bmi < 24.9:
            return "Normal weight"
        elif 25 <= self.bmi < 29.9:
            return "Overweight"
        else:
            return "Obesity"

class PatientUpdate(BaseModel):
    name: Annotated[Optional[str], Field(default=None)]
    city: Annotated[Optional[str], Field(default=None)]
    age: Annotated[Optional[int], Field(default=None, gt=0)]
    gender: Annotated[Optional[Literal['male', 'female', 'other']], Field(default=None)]
    height: Annotated[Optional[float], Field(default=None, gt=0)]
    weight: Annotated[Optional[float], Field(default=None, gt=0)]

    # Swagger pre-fills this instead of 0/"string", which would fail validation
    model_config = {"json_schema_extra": {"examples": [{"weight": 75.0}]}}

    @field_validator('gender', mode='before')
    @classmethod
    def lowercase_gender(cls, value):
        return value.lower() if isinstance(value, str) else value




def load_data():
    with open("patients.json", "r") as f:
        data =  json.load(f)
    return data

def save_data(data):
    with open("patients.json", "w") as f:
        json.dump(data, f, indent=4)

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

@app.post("/create")
def create_patient(patient: patient):
    data = load_data()
    if patient.id in data:
        raise HTTPException(status_code=400, detail=f"Patient with ID {patient.id} already exists.")
    data[patient.id] = patient.model_dump(exclude=['id'])
    save_data(data)
    return JSONResponse(status_code=201, content={"message": f"Patient with ID {patient.id} created successfully."})


@app.put("/update/{patient_id}")
def update_patient(patient_id: str, patient_update: PatientUpdate):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found.")

    existing_patient = data[patient_id]

    update_data = patient_update.model_dump(exclude_unset=True)

    for key, value in update_data.items():
        existing_patient[key] = value

    existing_patient['id'] = patient_id  # Ensure the ID remains unchanged
    patient_pydantic_object = patient(**existing_patient)  # Create a Pydantic object to compute BMI and verdict

    existing_patient = patient_pydantic_object.model_dump(exclude=['id'])  # Update the existing patient data with computed fields

    data[patient_id] = existing_patient

    save_data(data)
    return {"message": f"Patient with ID {patient_id} updated successfully."}

@app.delete("/delete/{patient_id}")
def delete_patient(patient_id: str):
    data = load_data()
    if patient_id not in data:
        raise HTTPException(status_code=404, detail=f"Patient with ID {patient_id} not found.")
    del data[patient_id]
    save_data(data)
    return {"message": f"Patient with ID {patient_id} deleted successfully."}

    


