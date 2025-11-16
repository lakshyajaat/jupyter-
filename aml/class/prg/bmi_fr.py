import streamlit as st
import requests

st.set_page_config(page_title="BMI Calculator", page_icon="⚖️", layout="centered")

st.title("BMI Calculator")
st.write("Enter your height and weight to calculate BMI and see the category.")

# --- Inputs ---
col1, col2 = st.columns(2)

with col1:
    height = st.number_input(
        "Height (meters)",
        min_value=0.5,
        max_value=2.5,
        value=1.70,
        step=0.01,
        format="%.2f",
        help="Enter height in meters (e.g., 1.75)"
    )

with col2:
    weight = st.number_input(
        "Weight (kg)",
        min_value=10.0,
        max_value=300.0,
        value=68.0,
        step=0.1,
        format="%.1f",
        help="Enter weight in kilograms (e.g., 68)"
    )

# Optional: call FastAPI endpoint
st.markdown("---")
use_api = st.checkbox("Send data to FastAPI endpoint (optional)")

api_url = ""
if use_api:
    api_url = st.text_input(
        "FastAPI URL",
        value="http://127.0.0.1:8000/bmi",
        help="Full URL to POST the BMI data (e.g., http://127.0.0.1:8000/bmi)"
    )

st.markdown("---")

# --- BMI calculation function ---
def calc_bmi(weight_kg: float, height_m: float):
    if height_m <= 0:
        return None
    bmi = weight_kg / (height_m ** 2)
    bmi_rounded = round(bmi, 2)
    if bmi < 18.5:
        category = "Underweight"
        severity = "info"
    elif 18.5 <= bmi < 24.9:
        category = "Normal weight"
        severity = "success"
    elif 25 <= bmi < 29.9:
        category = "Overweight"
        severity = "warning"
    else:
        category = "Obese"
        severity = "error"
    return bmi_rounded, category, severity

# --- Action button ---
if st.button("Calculate BMI"):
    result = calc_bmi(weight, height)
    if result is None:
        st.error("Please enter a valid height greater than 0.")
    else:
        bmi_val, category, severity = result

        # Display result with styling
        st.subheader("Result")
        st.write(f"**Height:** {height:.2f} m")
        st.write(f"**Weight:** {weight:.1f} kg")
        st.metric(label="BMI", value=f"{bmi_val}")

        if severity == "success":
            st.success(f"Category: {category}")
        elif severity == "info":
            st.info(f"Category: {category}")
        elif severity == "warning":
            st.warning(f"Category: {category}")
        else:
            st.error(f"Category: {category}")

        # Extra info
        st.markdown(
            """
            **BMI categories (WHO)**:
            - Underweight: &lt; 18.5  
            - Normal weight: 18.5 – 24.9  
            - Overweight: 25 – 29.9  
            - Obese: ≥ 30
            """
        )

        # Optionally POST to FastAPI
        if use_api and api_url:
            payload = {"height": height, "weight": weight}
            try:
                with st.spinner("Sending data to FastAPI..."):
                    resp = requests.post(api_url, json=payload, timeout=5)
                if resp.status_code == 200:
                    try:
                        data = resp.json()
                    except Exception:
                        st.error(f"FastAPI returned non-JSON response (status {resp.status_code}).")
                    else:
                        st.success("FastAPI response received:")
                        st.json(data)
                else:
                    st.error(f"FastAPI returned status {resp.status_code}: {resp.text}")
            except requests.exceptions.RequestException as e:
                st.error(f"Could not reach FastAPI at {api_url}. Error:\n{e}")

# --- Footer / run instructions ---
st.markdown("---")
st.caption("Tip: Run your FastAPI server with `uvicorn main:app --reload` if you want to use the optional API feature.")
