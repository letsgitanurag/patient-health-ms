import streamlit as st
import pandas as pd
from ml_utils import predict_verdict, load_data, save_patient
import plotly.express as px
import requests
import os

st.set_page_config(
    page_title="Patient Health Verdict System",
    page_icon="🏥",
    layout="wide"
)

# Custom CSS for modern UI
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
        color: #212529;
    }
    .stButton>button {
        background-color: #007bff;
        color: white;
        border-radius: 10px;
        border: none;
        padding: 10px 24px;
        font-weight: 600;
    }
    .stButton>button:hover {
        background-color: #0056b3;
    }
    .css-1d391kg {
        padding-top: 1rem;
    }
    h1, h2, h3 {
        color: #2c3e50;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏥 Patient Health Management System")
st.markdown("### AI-Powered Health Analysis & Verdict Prediction")

# Sidebar
with st.sidebar:
    st.header("Navigation")
    page = st.radio("Go to", ["Dashboard", "Verdict Predictor", "AI Health Assistant"])
    st.markdown("---")


if page == "Dashboard":
    st.header("Patient Records Analysis")
    
    # Load Data
    try:
        df = load_data()
        
        # Metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Patients", len(df))
        with col2:
            st.metric("Avg BMI", f"{df['bmi'].mean():.2f}")
        with col3:
            st.metric("Avg Age", f"{df['age'].mean():.1f}")
            
        st.markdown("---")
        
        # Data Table
        st.subheader("Patient Database")
        st.dataframe(df, use_container_width="stretch")
        
        # Visualizations
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("BMI Distribution")
            fig_bmi = px.histogram(df, x="bmi", nbins=10, title="BMI Distribution", color_discrete_sequence=['#007bff'])
            st.plotly_chart(fig_bmi, use_container_width=True)
            
        with col2:
            st.subheader("Weight vs Height")
            fig_scatter = px.scatter(df, x="height", y="weight", color="verdict", title="Weight vs Height by Verdict", size="bmi")
            st.plotly_chart(fig_scatter, use_container_width=True)
            
    except Exception as e:
        st.error(f"Error loading data: {e}")

elif page == "Verdict Predictor":
    st.header("Predict Patient Health Verdict")
    st.markdown("Enter patient details below to get an AI-generated health verdict.")
    
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            name = st.text_input("Patient Name")
            age = st.number_input("Age", min_value=1, max_value=120, value=25)
            gender = st.selectbox("Gender", ["male", "female"])
        
        with col2:
            height = st.number_input("Height (m)", min_value=0.5, max_value=2.5, value=1.70)
            weight = st.number_input("Weight (kg)", min_value=10.0, max_value=300.0, value=70.0)
            
        submit_button = st.form_submit_button("Predict Verdict")
        
    if submit_button:
        # Calculate BMI
        bmi = weight / (height ** 2)
        
        try:
            verdict = predict_verdict(age, gender, height, weight, bmi)
            
            # Store in session state for persistence
            st.session_state['last_prediction'] = {
                'name': name,
                'age': age,
                'gender': gender,
                'height': height,
                'weight': weight,
                'bmi': bmi,
                'verdict': verdict
            }
        except Exception as e:
             st.error(f"Prediction Error: {e}")

    # Display Result if exists
    if 'last_prediction' in st.session_state:
        pred = st.session_state['last_prediction']
        
        st.markdown("---")
        st.subheader("Prediction Result")
        
        col1, col2 = st.columns(2)
        with col1:
                st.metric("Calculated BMI", f"{pred['bmi']:.2f}")
        
        with col2:
            color = "green" if pred['verdict'] == "Normal" else "orange" if pred['verdict'] == "Overweight" else "red"
            st.markdown(f"<h3 style='color: {color};'>Verdict: {pred['verdict']}</h3>", unsafe_allow_html=True)
            
        if pred['verdict'] != "Normal":
            st.info("Recommendation: Please consult a nutritionist for a detailed health plan.")
        else:
            st.success("Great job! Maintain your current lifestyle.")
        
        # Save Button
        if st.button("Save Record to Database"):
            if not pred['name']:
                st.warning("Please enter a name to save the record.")
            else:
                try:
                    new_id = save_patient(
                        pred['name'], pred['age'], pred['gender'], 
                        pred['height'], pred['weight'], pred['bmi'], pred['verdict']
                    )
                    st.success(f"Patient record saved successfully! ID: {new_id}")
                    # Clear state to prevent double save
                    del st.session_state['last_prediction']
                    # Rerun to update dashboard data availability immediately
                    st.rerun()
                except Exception as e:
                    st.error(f"Error saving record: {e}")

elif page == "AI Health Assistant":
    st.header("AI Health Assistant 🤖")
    st.markdown("ask specific questions about your diet, exercise, or mental health.")
    
    # Using the provided API Key
    API_KEY = st.secrets["OPENROUTER_API_KEY"]
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = [
            {"role": "assistant", "content": "Hello! I'm your AI Health Assistant. How can I help you regarding your health, diet, or fitness today?"}
        ]
    
    # Display chat messages from history on app rerun
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    
    # React to user input
    if prompt := st.chat_input("Ask me for a diet plan, workout routine, etc..."):
        # Display user message in chat message container
        st.chat_message("user").markdown(prompt)
        # Add user message to chat history
        st.session_state.messages.append({"role": "user", "content": prompt})

        if not API_KEY:
             st.error("API Key is missing. Please add it to secrets.toml.")
             st.stop()

        # OpenRouter API Call
        try:
            headers = {
                "Authorization": f"Bearer {API_KEY}",
                "Content-Type": "application/json",
                 "HTTP-Referer": "http://localhost:8501", # Required for OpenRouter
                 "X-Title": "Patient Health App" # Optional
            }
            
            # Prepare messages for API
            # Filter out any initial message if it doesn't match the API expectation (though 'assistant' role is standard)
            api_messages = st.session_state.messages
            
            payload = {
                "model": "xiaomi/mimo-v2-flash:free",
                "messages": api_messages
            }

            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            
            if response.status_code == 200:
                data = response.json()
                assistant_message = data["choices"][0]["message"]["content"]
                
                # Display assistant response in chat message container
                with st.chat_message("assistant"):
                    st.markdown(assistant_message)
                
                # Add assistant response to chat history
                st.session_state.messages.append({"role": "assistant", "content": assistant_message})
            elif response.status_code == 401:
                st.error("Authentication Error (401): The API Key provided is invalid or expired. Please check your key in `.streamlit/secrets.toml`.")
            else:
                 st.error(f"Error from API: {response.status_code} - {response.text}")
            
        except Exception as e:
             st.error(f"Error generating response: {e}")



