# backend/main.py
from fastapi import FastAPI
from pydantic import BaseModel
import uvicorn

# Create FastAPI instance
app = FastAPI(title="Sentiment Analyzer API")

# Define input model
class TextInput(BaseModel):
    text: str

# Basic home route
@app.get("/")
def home():
    return {"message": "FastAPI backend is running successfully!"}

# POST endpoint for text analysis
@app.post("/analyze/")
def analyze_text(data: TextInput):
    text = data.text.lower()

    # Simple rule-based sentiment analysis
    if "good" in text or "happy" in text or "great" in text:
        sentiment = "Positive 😊"
    elif "bad" in text or "sad" in text or "angry" in text:
        sentiment = "Negative 😞"
    else:
        sentiment = "Neutral 😐"

    return {"sentiment": sentiment}


# Run the FastAPI app
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
