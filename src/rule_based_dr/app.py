import streamlit as st
import json
from db import get_available_symptoms_list
from service import run_diagnostic_flow

st.set_page_config(
    page_title="Medical Diagnostic System",
    page_icon="⚕️",
    layout="wide",
    initial_sidebar_state="expanded"
)

def main():
    st.title("🩺 Patient Intake and Diagnosis Dashboard")
    st.markdown("---")

    # Layout for Form and Results
    col_input, col_output = st.columns([1, 1.2])

    with col_input:
        st.header("Patient Intake Form")
        st.write("Please fill out the patient's demographic and symptomatic details.")

        with st.form("intake_form"):
            # Demographics
            st.subheader("Demographics")
            name = st.text_input("Patient Name", placeholder="e.g. John Doe")
            
            row1_col1, row1_col2 = st.columns(2)
            with row1_col1:
                age = st.number_input("Age", min_value=0, max_value=120, value=30, step=1)
            with row1_col2:
                gender = st.selectbox("Gender", ["Male", "Female", "Other"])

            st.write("")
            # Symptoms
            st.subheader("Symptoms")
            
            # Fetch available symptoms from DB or mock
            available_symptoms = get_available_symptoms_list()
            
            selected_symptom_names = st.multiselect(
                "Select Reported Symptoms",
                options=available_symptoms,
                help="Choose all symptoms the patient is currently experiencing."
            )
            
            # Dynamic severity inputs
            symptoms_list = []
            if selected_symptom_names:
                st.write("Specify Severity for Selected Symptoms:")
                for symp in selected_symptom_names:
                    sev = st.select_slider(
                        f"Severity for **{symp}**",
                        options=["Low", "Medium", "High", "Critical"],
                        value="Medium",
                        key=f"slider_{symp}"
                    )
                    symptoms_list.append({"name": symp, "severity": sev})
            else:
                st.info("No symptoms selected yet.")

            st.markdown("---")
            submitted = st.form_submit_button("Run Diagnosis", use_container_width=True)

    with col_output:
        st.header("Diagnostic Results")
        
        if submitted:
            if not name.strip():
                st.error("Patient Name is required.")
            elif not symptoms_list:
                st.warning("Please select at least one symptom to run a diagnosis.")
            else:
                patient_data = {
                    "name": name,
                    "age": age,
                    "gender": gender
                }
                
                with st.spinner("Analyzing rules & probabilities..."):
                    # Execute backend flow
                    try:
                        result_json = run_diagnostic_flow(patient_data, symptoms_list)
                        result_data = json.loads(result_json)
                        
                        diagnoses = result_data.get("diagnoses", [])
                        
                        st.success(f"Diagnosis complete! Patient ID mapping: `{result_data.get('patient_id')}`")
                        
                        if not diagnoses:
                            st.info("No matching diseases found based on current rules.")
                        else:
                            # Render beautiful output
                            st.subheader("Ranked Candidates")
                            for idx, diag in enumerate(diagnoses):
                                disease_name = diag.get("disease_name")
                                score = diag.get("confidence_score", 0)
                                desc = diag.get("description")
                                treatment = diag.get("recommended_treatment")
                                
                                # Highlight top result
                                border_color = "primary" if idx == 0 else "secondary"
                                
                                with st.expander(f"**Rank {idx+1}: {disease_name}** - Confidence: {score:.1f}%", expanded=(idx==0)):
                                    st.progress(min(score / 100.0, 1.0))
                                    st.write(f"**Description:** {desc}")
                                    st.write(f"**Recommended Treatment:** {treatment}")
                            
                            st.write("")
                            st.subheader("Raw JSON Response")
                            st.json(result_data)
                            
                    except Exception as e:
                        st.error(f"An error occurred during diagnosis: {e}")
        else:
             st.info("Fill out the intake form and click 'Run Diagnosis' to view results.")

if __name__ == "__main__":
    main()
