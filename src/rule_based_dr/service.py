import json
from db import (
    create_patient,
    insert_patient_symptoms,
    get_symptom_weights,
    get_diagnostic_rules,
    get_probability_table,
    get_disease_details,
    save_diagnosis_ranks
)

def prioritize_symptoms(symptoms_list, default_weights):
    """
    Symptom Prioritization node:
    Expects symptoms_list like [{"name": "Fever", "severity": "High"}]
    Merges with DB weights.
    """
    weighted_symptoms = []
    
    # Map raw weights to a lookup
    weight_lookup = {w.get("symptom_name"): w for w in default_weights}
    
    severity_multiplier = {"Low": 0.5, "Medium": 1.0, "High": 1.5, "Critical": 2.0}
    
    for symptom in symptoms_list:
        name = symptom.get("name")
        severity = symptom.get("severity", "Medium")
        
        # Default weight if missing from DB
        base_weight = 1.0
        if name in weight_lookup:
             base_weight = weight_lookup[name].get("weight_value", 1.0)
        
        calculated_severity = base_weight * severity_multiplier.get(severity, 1.0)
        
        weighted_symptoms.append({
            "name": name,
            "severity": severity,
            "calculated_severity": calculated_severity
        })
        
    return weighted_symptoms

def _calculate_if_then_branch(weighted_symptoms, rules):
    """
    Branch 1: Execute IF-THEN Diagnostic Rules
    Mock engine to map rules against symptoms
    """
    scores = {}
    symptom_names = [s["name"] for s in weighted_symptoms]
    
    # Very basic static rules fallback if the database has none
    if not rules:
        rules = [
            {"disease_id": "D1", "disease_name": "Flu", "conditions": ["Fever", "Cough"]},
            {"disease_id": "D2", "disease_name": "Migraine", "conditions": ["Headache", "Nausea"]},
            {"disease_id": "D3", "disease_name": "COVID-19", "conditions": ["Fever", "Cough", "Shortness of Breath", "Fatigue"]}
        ]
        
    for rule in rules:
        # A simple condition check (e.g., matching condition array vs actual array)
        conditions = rule.get("conditions", [])
        disease = rule.get("disease_name")
        
        match_count = sum([1 for c in conditions if c in symptom_names])
        if match_count > 0:
            # Score logic: percentage of rule conditions matched
            score = (match_count / len(conditions)) * 100
            scores[disease] = score
            
    return scores

def _calculate_bayesian_branch(weighted_symptoms, prob_table):
    """
    Branch 2: Execute Bayesian Probability calculations.
    Returns disease mapping to confidence score.
    """
    # Extremely simplified Mock Bayesian table execution if DB is empty
    scores = {}
    symptom_names = [s["name"] for s in weighted_symptoms]
    
    # Mock base prior probabilities mapping
    priors = {"Flu": 0.1, "Migraine": 0.05, "COVID-19": 0.15, "Common Cold": 0.3}
    
    if not prob_table:
         prob_table = [
            {"symptom": "Fever", "Flu": {"sensitivity": 0.8}, "COVID-19": {"sensitivity": 0.9}},
            {"symptom": "Cough", "Flu": {"sensitivity": 0.7}, "COVID-19": {"sensitivity": 0.8}, "Common Cold": {"sensitivity": 0.9}},
            {"symptom": "Headache", "Migraine": {"sensitivity": 0.9}, "Flu": {"sensitivity": 0.5}},
            {"symptom": "Fatigue", "COVID-19": {"sensitivity": 0.85}, "Flu": {"sensitivity": 0.7}}
         ]
         
    # Iteratively map the posterior
    for disease, prior in priors.items():
        posterior = prior
        # Multiply likelihoods for each matched symptom
        for symp in symptom_names:
            for pt in prob_table:
                if pt.get("symptom") == symp:
                    # Get sensitivity for this specific disease if it exists
                    disease_data = pt.get(disease)
                    if isinstance(disease_data, dict):
                        sensitivity = disease_data.get("sensitivity", 0.01)
                    else:
                        sensitivity = 0.01
                        
                    posterior *= float(sensitivity)
        
        # Give mock boost to posterior just for UI rendering visualization scaling
        if posterior > prior: 
            scores[disease] = min(posterior * 500.0, 100.0) # Cap at 100%
            
    return scores
    
def _merge_and_normalize(if_then_scores, bayesian_scores):
    """Merges logic from the two branches."""
    final_scores = {}
    all_diseases = set(list(if_then_scores.keys()) + list(bayesian_scores.keys()))
    
    for disease in all_diseases:
        if_score = if_then_scores.get(disease, 0)
        bayes_score = bayesian_scores.get(disease, 0)
        
        # Simple weighted average
        # E.g. 60% weight to IF-THEN, 40% weight to Bayesian
        final_scores[disease] = round((if_score * 0.6) + (bayes_score * 0.4), 2)
        
    return final_scores

def fetch_enriched_disease_details(ranked_diseases_list):
    """Disease Enrichment node. Joins scores with full Disease descriptions."""
    disease_names = [r["disease"] for r in ranked_diseases_list]
    db_details = get_disease_details(disease_names)
    
    # Fallback default descriptions for demo rendering if DB is empty
    default_details = {
        "Flu": {"description": "Influenza is a viral infection that attacks your respiratory system.", "treatment": "Rest, hydration, antiviral drugs."},
        "Migraine": {"description": "A neurological condition that can cause multiple symptoms.", "treatment": "Pain-relieving medications, triptans."},
        "COVID-19": {"description": "Infectious disease caused by the SARS-CoV-2 virus.", "treatment": "Isolation, rest, and fluid intake. Seek medical care if severe."},
        "Common Cold": {"description": "A mild viral infection of the nose and throat.", "treatment": "Rest, drink fluids, OTC cold medicines."},
    }
    
    enriched = []
    for diag in ranked_diseases_list:
        disease_name = diag["disease"]
        
        details = db_details.get(disease_name) or default_details.get(disease_name, {"description": "No description available.", "treatment": "Consult a physician."})
        
        enriched.append({
            "disease_name": disease_name,
            "confidence_score": diag["score"],
            "description": details.get("description"),
            "recommended_treatment": details.get("treatment")
        })
        
    return enriched

def run_diagnostic_flow(patient_data: dict, symptoms_list: list):
    """
    API Gateway/Controller entry point.
    Executes the entire backend flow diagram logic.
    """
    
    # 1. Start: Receive Request - Fetch context
    # Get DB collections context
    weights = get_symptom_weights()
    rules = get_diagnostic_rules()
    probabilities = get_probability_table()
    
    # 2. Symptom Prioritization
    weighted_symptoms = prioritize_symptoms(symptoms_list, weights)
    
    # 3. Inference Engine (Parallel Branches)
    if_then_scores = _calculate_if_then_branch(weighted_symptoms, rules)
    bayesian_scores = _calculate_bayesian_branch(weighted_symptoms, probabilities)
    
    # Normalize
    merged_scores = _merge_and_normalize(if_then_scores, bayesian_scores)
    
    # 4. Final Ranking & Sorting
    # Sort diseases by highest confidence score
    sorted_diagnoses = sorted(
        [{"disease": k, "score": v} for k, v in merged_scores.items() if v > 0],
        key=lambda x: x["score"],
        reverse=True
    )
    
    # 5. Disease Enrichment
    enriched_results = fetch_enriched_disease_details(sorted_diagnoses)
    
    # 6. Finalization (Save Results via DB)
    patient_id = create_patient(
        name=patient_data.get("name"),
        age=patient_data.get("age"),
        gender=patient_data.get("gender")
    )
    
    if patient_id:
         insert_patient_symptoms(patient_id, weighted_symptoms)
         # Save confirmation records
         save_diagnosis_ranks(patient_id, enriched_results)
    
    # 7. End: Send Response to Client
    return json.dumps({
        "status": "success",
        "patient_id": patient_id,
        "diagnoses": enriched_results
    }, indent=2)
