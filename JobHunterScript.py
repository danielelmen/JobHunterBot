import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai
import openai

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
email_text = st.text_area("Insæt job annonce:")

def load_system_prompt(file_path="system_prompt.txt"):
    with open(file_path, "r", encoding="utf-8") as f:
        return f.read()

system_prompt = load_system_prompt()

if st.button("Generér jobansøgning"):
    if email_text.strip() == "":
        st.warning("Du skal indsætte en jobannonce.")
    else:
        with st.spinner("Genererer ansøgning..."):

            # Brug OpenAI GPT-4
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",  # or gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": email_text}
                ],
                temperature=0.7,
                max_tokens=1000
            )

            application_text = response["choices"][0]["message"]["content"]
            st.success("Her er dit forslag til ansøgning:")
            st.text_area("Jobansøgning", application_text, height=300)
