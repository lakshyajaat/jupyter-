from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class BMIData(BaseModel):
    height: float  # in meters
    weight: float  # in kilograms

@app.get("/")
def info():
    return {"message": "Welcome to the BMI Calculator API! Use POST /bmi with your height and weight."}

@app.post("/bmi")
def calculate_bmi(data: BMIData):
    bmi = data.weight / (data.height ** 2)

    if bmi < 18.5:
        category = "Underweight"
    elif 18.5 <= bmi < 24.9:
        category = "Normal weight"
    elif 25 <= bmi < 29.9:
        category = "Overweight"
    else:
        category = "Obese"

    return {
        "height (m)": data.height,
        "weight (kg)": data.weight,
        "BMI": round(bmi, 2),
        "Category": category
    }
