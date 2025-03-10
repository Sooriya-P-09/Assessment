import streamlit as st
import pandas as pd
import pickle
import json
import os
import google.generativeai
# Set your Gemini API Key directly
genai=google.generativeai
API_KEY = st.secrets["API_KEY"] # Replace with your actual Gemini API key
genai.configure(api_key=API_KEY)

# Validate user login
def validate_user(user_id):
    return "@agilisium" in user_id

# Generate a coding question using Gemini
def generate_question(prompt):
    try:
        # Structured prompt with clear instructions
        structured_prompt = (
            f"Generate a Python coding question based on the topic: '{prompt}'. "
            "Your response must be a JSON object with the following keys: "
            "'question', 'sample_input', and 'expected_output'. "
            "Return only the JSON object, without any additional text or explanations. "
            "Example Output: "
            '{"question": "Write a function to find the factorial of a number.", '
            '"sample_input": "5", "expected_output": "120"}'
        )

        # Use Gemini to generate the question
        model = genai.GenerativeModel('gemini-1.5-pro-001')
        response = model.generate_content(structured_prompt)

        # Extract raw text response
        generated_text = response.text.strip()

        # Debugging Output
        print("Raw AI Response:", generated_text)

        # Clean response to extract JSON
        json_start = generated_text.find("{")
        json_end = generated_text.rfind("}") + 1

        if json_start == -1 or json_end == -1:
            print("Error: No JSON object found in the response.")
            return "Error: No JSON object found in the response."

        cleaned_text = generated_text[json_start:json_end]

        # Debugging Output
        print("Cleaned Response:", cleaned_text)

        # Parse JSON response
        try:
            generated_data = json.loads(cleaned_text)
            question = generated_data.get("question", "").strip()
            sample_input = generated_data.get("sample_input", "").strip()
            sample_output = generated_data.get("expected_output", "").strip()

            if question and sample_input and sample_output:
                return question, sample_input, sample_output
            else:
                print("Error: AI response is missing required fields.")
                return "Error: AI response is missing required fields."

        except json.JSONDecodeError as e:
            print(f"JSON Parsing Error: {e}")
            return f"Error: Failed to parse AI response as JSON. Response: {cleaned_text}"

    except Exception as e:
        print(f"API Error: {e}")
        return f"API Error: {e}"

# Save and Load Questions
def save_questions():
    with open("session_questions.pkl", "wb") as f:
        pickle.dump(st.session_state["questions"], f)

def load_questions():
    try:
        with open("session_questions.pkl", "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return []

# Admin Dashboard
def admin_dashboard():
    st.header("Admin Dashboard")

    if "questions" not in st.session_state:
        st.session_state["questions"] = []

    # Set candidate password
    common_password = st.text_input("Set Common Candidate Password", type="password")
    if st.button("Save Password"):
        with open("candidate_password.txt", "w") as f:
            f.write(common_password)
        st.success("Common Password Saved Successfully")

    # Question Generation Section
    st.subheader("Create Questions")
    prompt = st.text_area("Enter a prompt to generate a question")

    if st.button("Generate Question"):
        if prompt:
            result = generate_question(prompt)
            if isinstance(result, tuple) and len(result) == 3:
                question, sample_input, sample_output = result
                st.session_state["questions"].append((question, sample_input, sample_output))
                save_questions()
                st.success("New Question Generated and Saved Successfully")
            else:
                st.error(result)  # Show the error message returned by generate_question

    # Show saved questions
    if st.session_state["questions"]:
        st.subheader("Existing Questions")
        for i, (question, sample_input, sample_output) in enumerate(st.session_state["questions"], 1):
            st.write(f"**Question {i}:** {question}")
            st.text(f"Sample Input: {sample_input}")
            st.text(f"Expected Output: {sample_output}")

# Candidate Dashboard
def candidate_page():
    st.header("Candidate Dashboard")

    if "questions" not in st.session_state or not st.session_state["questions"]:
        st.session_state["questions"] = load_questions()

    if not st.session_state["questions"]:
        st.warning("No new questions available. Please wait for the admin to add questions.")
    else:
        for index, (question, sample_input, sample_output) in enumerate(st.session_state["questions"]):
            st.subheader(f"Question {index + 1}")
            st.write(question)
            st.text(f"Sample Input: {sample_input}")
            st.text(f"Expected Output: {sample_output}")

            code = st.text_area(f"Write your code for Question {index + 1}", key=f"code_{index}")

            if st.button(f"Run Code {index + 1}"):
                try:
                    # Execute user code safely
                    local_vars = {}
                    exec(code, {}, local_vars)

                    # Convert output to string for comparison
                    output = str(local_vars.get("output", "")).strip()
                    expected_output = sample_output.strip()

                    if output == expected_output:
                        st.success("Correct Output! Your code worked.")
                    else:
                        st.error(f"Incorrect Output! Expected: {expected_output}, Got: {output}")
                except Exception as e:
                    st.error(f"Error running code: {e}")

# Main Function: Login & Navigation
def main():
    st.title("Login Page")

    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False

    if not st.session_state["logged_in"]:
        user_type = st.selectbox("Select User Type", ["Admin", "Candidate"])
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
                        st.error("Candidate Password Not Set by Admin")

    if st.session_state["logged_in"]:
        if st.session_state["user_type"] == "Admin":
            admin_dashboard()
        else:
            candidate_page()

if __name__ == "__main__":
    main()
