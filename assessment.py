import streamlit as st
import pandas as pd
import pickle
import json
import google.generativeai

# ✅ Load API Key from Streamlit Secrets
API_KEY = st.secrets["API_KEY"]  # Ensure it's set in .streamlit/secrets.toml
google.generativeai.configure(api_key=API_KEY)

# ✅ Validate User Login
def validate_user(user_id):
    return "@agilisium" in user_id

# ✅ Generate Coding Question
def generate_question(prompt):
    try:
        structured_prompt = (
            f"Generate a Python coding question based on: '{prompt}'. "
            "Your response must be a JSON object with keys: 'question', 'sample_input', 'expected_output'. "
            "Return only the JSON, nothing else."
        )
        model = genai.GenerativeModel('gemini-1.5-pro-001')
        response = model.generate_content(structured_prompt)
        generated_text = response.text.strip()

        # 🔍 Extract JSON from Response
        json_start = generated_text.find("{")
        json_end = generated_text.rfind("}") + 1
        if json_start == -1 or json_end == -1:
            return "Error: No JSON object found in AI response."

        cleaned_text = generated_text[json_start:json_end]
        generated_data = json.loads(cleaned_text)

        return (
            generated_data.get("question", ""),
            generated_data.get("sample_input", ""),
            generated_data.get("expected_output", ""),
        )
    except Exception as e:
        return f"API Error: {e}"

# ✅ Save and Load Questions
def save_questions():
    with open("session_questions.pkl", "wb") as f:
        pickle.dump(st.session_state["questions"], f)

def load_questions():
    try:
        with open("session_questions.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []

# ✅ Admin Dashboard
def admin_dashboard():
    st.header("Admin Dashboard")

    if "questions" not in st.session_state:
        st.session_state["questions"] = []

    # Candidate Password Setup
    common_password = st.text_input("Set Candidate Password", type="password")
    if st.button("Save Password"):
        with open("candidate_password.txt", "w") as f:
            f.write(common_password)
        st.success("Password Saved")

    # Question Generation
    st.subheader("Create Questions")
    prompt = st.text_area("Enter a prompt")

    if st.button("Generate Question"):
        if prompt:
            result = generate_question(prompt)
            if isinstance(result, tuple):
                st.session_state["questions"].append(result)
                save_questions()
                st.success("Question Generated & Saved")
            else:
                st.error(result)

    # Show Questions
    if st.session_state["questions"]:
        st.subheader("Existing Questions")
        for i, (question, sample_input, sample_output) in enumerate(st.session_state["questions"], 1):
            st.write(f"**Q{i}:** {question}")
            st.text(f"Sample Input: {sample_input}")
            st.text(f"Expected Output: {sample_output}")

# ✅ Candidate Dashboard
def candidate_page():
    st.header("Candidate Dashboard")

    if "questions" not in st.session_state:
        st.session_state["questions"] = load_questions()

    if not st.session_state["questions"]:
        st.warning("No questions available.")
    else:
        for index, (question, sample_input, sample_output) in enumerate(st.session_state["questions"]):
            st.subheader(f"Question {index + 1}")
            st.write(question)
            st.text(f"Sample Input: {sample_input}")
            st.text(f"Expected Output: {sample_output}")

            # ✅ Store User Code in Session State
            if f"code_{index}" not in st.session_state:
                st.session_state[f"code_{index}"] = ""

            user_code = st.text_area(f"Write your code for Q{index + 1}", value=st.session_state[f"code_{index}"], key=f"code_{index}")

            if st.button(f"Run Code {index + 1}"):
                try:
                    local_vars = {}
                    exec(user_code, {}, local_vars)  # **Security Risk!**
                    output = str(local_vars.get("output", "")).strip()

                    if output == sample_output.strip():
                        st.success("✅ Correct Output!")
                    else:
                        st.error(f"❌ Incorrect! Expected: {sample_output}, Got: {output}")
                except Exception as e:
                    st.error(f"Error: {e}")

# ✅ Main: Login & Navigation
def main():
    st.title("Login Page")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        user_type = st.selectbox("User Type", ["Admin", "Candidate"])
        user_id = st.text_input("User ID")
        password = st.text_input("Password", type="password")

        if st.button("Login"):
            if not validate_user(user_id):
                st.error("Invalid User ID! Must contain '@agilisium'")
            else:
                if user_type == "Admin":
                    if password == "admin123":
                        st.session_state["logged_in"] = True
                        st.session_state["user_type"] = "Admin"
                        st.success("Admin Login Successful")
                else:
                    try:
                        with open("candidate_password.txt", "r") as f:
                            common_password = f.read().strip()
                        if password == common_password:
                            st.session_state["logged_in"] = True
                            st.session_state["user_type"] = "Candidate"
                            st.success("Candidate Login Successful")
                        else:
                            st.error("Incorrect Candidate Password")
                    except FileNotFoundError:
                        st.error("Candidate Password Not Set")

    if st.session_state["logged_in"]:
        if st.session_state["user_type"] == "Admin":
            admin_dashboard()
        else:
            candidate_page()

if __name__ == "__main__":
    main()
