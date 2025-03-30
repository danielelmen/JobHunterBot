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
website = st.text_area("Indsæt link til virksomheden:")

def call_openai(system_prompt, user_input, model="gpt-4o-mini", max_tokens=500, temperature=0.7, api_key=None, use_tools=False):
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

    if use_tools:
        data["tools"] = [{"type": "web-search-preview"}]

    try:
        response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=data)
        response.raise_for_status()  # Raises HTTPError for bad responses
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as http_err:
        return f"⚠️ API-fejl: {response.status_code} - {response.text}"

# Load prompt
with open("system_website.txt", "r", encoding="utf-8") as file:
    website_prompt = file.read().strip()

# Get API key
api_key = st.secrets["api_keys"]["oakey"]

if st.button("Analysér"):
    if website.strip():
        with st.spinner("Analysér opslaget og virksomheden"):
            output = call_openai(
                system_prompt=website_prompt,
                user_input=website,
                model="gpt-4o",
                max_tokens=700,
                temperature=0.7,
                api_key=api_key,
                use_tools=True  # Aktiverer 'web-search-preview'
            )
            st.text_area("Information om virksomheden:", output, height=300)
    else:
        st.warning("Indsæt venligst et link:")