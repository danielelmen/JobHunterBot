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

# Initialiser status for analyse
if "analyse_done" not in st.session_state:
    st.session_state["analyse_done"] = False

# Get OpenAI key og konfigurer
openai_key = st.secrets["api_keys"]["oakey"]
genai.configure(api_key=openai_key)

# Titel og inputfelter
st.title("JobHunterBot")
st.write("Work smarter not harder")
job_ad = st.text_area("Indsæt job annonce:")
job_om = st.text_area("Indsæt information om virksomheden:")

# Funktion til API-kald
def call_openai(system_prompt, user_input, model="gpt-4o-mini", max_tokens=500, temperature=0.7, api_key=None):
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
        response.raise_for_status()
        return response.json()["choices"][0]["message"]["content"].strip()
    except requests.exceptions.HTTPError as http_err:
        return f"⚠️ API-fejl: {response.status_code} - {response.text}"

# Indlæs analyse-prompt
with open("system_analyse.txt", "r", encoding="utf-8") as file:
    analyse_prompt = file.read().strip()

# Analyseknap
if st.button("Analysér"):
    if job_om.strip() and job_ad.strip():
        with st.spinner("Vent mens der analyseres..."):
            analyse_output = call_openai(
                system_prompt=analyse_prompt,
                user_input=f"Jobannonce:\n{job_ad}\n\nVirksomhedsbeskrivelse:\n{job_om}",
                model="gpt-4o-mini",
                max_tokens=700,
                temperature=0.7,
                api_key=openai_key
            )
            st.session_state["analyse_output"] = analyse_output
            st.session_state["analyse_done"] = True
            st.text_area("🔍 Analyse af job og virksomhed:", analyse_output, height=500)
    else:
        st.warning("Indsæt information i begge felter:")

# Hvis analyse allerede er lavet
analyse_output = st.session_state.get("analyse_output", "")
analyse_done = st.session_state.get("analyse_done", False)

# Vis valg og ansøgning kun efter analyse
if analyse_done:
    # Valg af ansøgningstype
    valg = st.radio(
        "Vælg typen af ansøgning:",
        ("Klassisk", "Alternativ")
    )

    # Indlæs systeminstruktion baseret på valg
    if valg == "Klassisk":
        with open("system_ansog_klassisk.txt", "r", encoding="utf-8") as file:
            ansogning_eksempel = file.read().strip()
    elif valg == "Alternativ":
        with open("system_ansog_alternativ.txt", "r", encoding="utf-8") as file:
            ansogning_eksempel = file.read().strip()

    with open("system_ansog_main.txt", "r", encoding="utf-8") as file:
        ansog_prompt = file.read().strip()

    with open("info_cv.txt", "r", encoding="utf-8") as file:
        cv_prompt = file.read().strip()

    with open("info_generelt.txt", "r", encoding="utf-8") as file:
        generelt_prompt = file.read().strip()        
    #Sammensætter dynamisk system instruktion
    custom_prompt = f"""
    {ansog_prompt} #Du er en... og skal...
    Her kan du se en tidligere ansøgning jeg har skrevet som er virkelig god. Du skal matche sproget og stilen meget tæt og bruge denne som reference: {ansogning_eksempel}

    Her kan du se et overskueligt overblik over mit CV
    {cv_prompt}

    Jeg har skrevet dette dokument, for at kunne give så meget relevant information som overhoved muligt:
    {generelt_prompt}

    Du skal bruge indsatte informationer til at skrive ansøgningen, og det er meget vigtigt at du skriver på præcis samme måde som at jeg skriver. Lav ikke en overskrift. Indsæt ikke ansøgninger i kvotationstegn. Afslut ikke med venlig hilsen eller telefon nummer etc. Vis kune selve brødteksten.
    """

#f""" Du modtager en tekstfil med information om en job og fakta om virksomheden som jeg skal til at søge. Du skal nu udtrække de information som er relevante fra dette CV til jobbet: {cv_prompt}. Dit output skal være det samme format som i CV'et."""

    # Knappen til at generere ansøgning
    if st.button("Generér ansøgning"):
        if analyse_output.strip():
            with st.spinner("Matcher ansøgning med dine kompetencer..."):
                match_output = call_openai(
                    system_prompt=custom_prompt,
                    user_input=analyse_output,
                    model="gpt-4o",
                    max_tokens=16384,
                    temperature=0.7,
                    api_key=openai_key
                )
                st.text_area("✉️ Forslag til ansøgning:", match_output, height=300)
        else:
            st.warning("Du skal analysere først, før du kan generere en ansøgning.")
