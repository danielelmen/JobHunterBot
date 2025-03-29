import streamlit as st
import fitz  # PyMuPDF
import google.generativeai as genai

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

# Load API key securely
try:
    gemini_key = st.secrets["api_keys"]["gemini"]
    genai.configure(api_key=gemini_key)
except KeyError:
    st.error("API-nøgle mangler i secrets!")
    st.stop()

# Funktion til at læse systeminstruktion
def read_system_instruction():
    return "Du er en hjælpsom AI, der opsummerer tekst."

# Funktion til at ekstrahere tekst fra PDF
def extract_text_from_pdf(pdf_file):
    doc = fitz.open(stream=pdf_file.read(), filetype="pdf")
    text = "\n".join([page.get_text("text") for page in doc])
    return text

# Funktion til at sende tekst til Gemini AI
def process_text_with_gemini(text, system_instruction):
    prompt = f"{system_instruction}\n\n{text}"
    model = genai.GenerativeModel("gemini-2.0-flash")
    response = model.generate_content(prompt)
    return response.text if response else "Ingen respons fra AI."

def main():
    st.title("PDF/Text BreakDownBot")
    st.write(f"Velkommen, {st.session_state['username']}! Upload en PDF-fil eller indsæt tekst, og vælg hvordan du vil behandle input.")

    uploaded_file = st.file_uploader("Vælg en PDF-fil", type="pdf")
    user_text = st.text_area("Eller indsæt/skrive tekst her", "")

    # Checkbox-muligheder for forskellige AI-behandlinger
    ai_english = st.checkbox("AI English: Summarize the text in English")
    ai_danish = st.checkbox("AI Danish: Summarize the text in Danish")
    ai_german = st.checkbox("AI German: Summarize the text in German")

    if st.button("Generer Opsummering"): 
        with st.spinner("AI analyserer teksten..."):
            extracted_text = extract_text_from_pdf(uploaded_file) if uploaded_file else user_text
            
            responses = {}
            if ai_english:
                responses["English"] = process_text_with_gemini(extracted_text, "Summarize the text in English")
            if ai_danish:
                responses["Danish"] = process_text_with_gemini(extracted_text, "Summarize the text in Danish")
            if ai_german:
                responses["German"] = process_text_with_gemini(extracted_text, "Summarize the text in German")

            for lang, response in responses.items():
                st.subheader(f"AI's Opsummering ({lang})")
                st.text_area(f"Opsummering på {lang}", response, height=150)

if __name__ == "__main__":
    main()