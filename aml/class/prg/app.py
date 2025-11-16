# frontend/app.py
import streamlit as st
import requests

# Streamlit title
st.title("🧠 Sentiment Analyzer (FastAPI + Streamlit)")

# User input text box
user_input = st.text_area("Enter some text to analyze:")

# When button clicked
if st.button("Analyze"):
    if user_input.strip() == "":
        st.warning("⚠️ Please enter some text before analyzing.")
    else:
        try:
            # Send data to FastAPI backend
            response = requests.post(
                "http://127.0.0.1:8000/analyze/",
                json={"text": user_input}
            )

            # Process response
            if response.status_code == 200:
                result = response.json()
                st.success(f"✅ Sentiment: {result['sentiment']}")
            else:
                st.error("❌ Error: Could not get response from FastAPI backend.")
        except Exception as e:
            st.error(f"⚠️ Connection error: {e}")
