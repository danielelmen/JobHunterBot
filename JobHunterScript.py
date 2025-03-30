import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import requests

# Hent brugere fra secrets
users = st.secrets.get("users", {})

def authenticate():
    """Håndterer login med en sikker og stabil metode."""
    if "authenticated" not in st.session_state:
        st.session_state["authenticated"] = False
    if "username" not in st.session_state:
        st.session_state["username"] = ""
    
    if not st.session_state["authenticated"]:
        st.title("Log ind")
        username = st.text_input("Brugernavn")
        password = st.text_input("Adgangskode", type="password")
        
        if st.button("Login"):
            if username in users and users[username] == password:
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.success("Login lykkedes! Appen genindlæses...")
                st.rerun()  # Tvinger en opdatering af appen
            else:
                st.error("Forkert brugernavn eller adgangskode")
        
        st.stop()

authenticate()

#Get open ai key
openai_key = st.secrets["api_keys"]["oakey"]
genai.configure(api_key=openai_key)


# Titles
st.title("JobHunterBot")
st.write("Work smarter not harder")

# Input text area
job_ad = st.text_area("Indsæt job annonce:")

def call_openai(system_prompt, user_input, model="gpt-4o-mini", max_tokens=500, temperature=0.7, api_key=None):
    """Sends a prompt to the OpenAI API and returns the assistant's reply."""
    
    if api_key is None:
        raise ValueError("API key is missing.")

    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {api_key}'
    }

    data = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ],
        "max_tokens": max_tokens,
        "temperature": temperature
    }

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"⚠️ Fejl i API-kald: {str(e)}"

# Load prompt
with open("system_prompt.txt", "r", encoding="utf-8") as file:
    job_prompt = file.read().strip()

# Get API key
api_key = st.secrets["api_keys"]["oakey"]

if st.button("Generér ansøgning"):
    if job_ad.strip():
        with st.spinner("Genererer ansøgning..."):
            output = call_openai(
                system_prompt=job_prompt,
                user_input=job_ad,
                model="gpt-4o-mini",
                max_tokens=700,
                temperature=0.7,
                api_key=api_key
            )
            st.text_area("💡 Forslag til ansøgning:", output, height=300)
    else:
        st.warning("Indsæt venligst en jobannonce.")


#Save the letter to the computer
downloadtxt = "Dear Hiring Manager,\n\nI'm excited to apply for the..."

# Create the download button
st.download_button(
    label="Download your job application letter",
    data=downloadtxt,
    file_name="application_letter.pdf",  # You could also use .docx or .pdf
    mime="text/plain"  # Change this depending on your format
)