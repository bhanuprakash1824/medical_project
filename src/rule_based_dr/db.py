import streamlit as st
import pymongo
from pymongo.errors import ServerSelectionTimeoutError
from datetime import datetime
import pandas as pd

# Global client
client = None

@st.cache_resource(show_spinner="Connecting to database...")
def init_connection():
    try:
        uri = st.secrets["uri"]
        client = pymongo.MongoClient(uri, serverSelectionTimeoutMS=5000)
        # Force a call to check if connection is active
        client.server_info()
        return client
    except Exception as e:
        st.error(f"Failed to connect to MongoDB: {e}")
        return None

def get_db():
    global client
    if client is None:
        client = init_connection()
    if client:
        return client.get_database("medical_diagnostic_system")
    return None

def get_collection(collection_name):
    db = get_db()
    if db is not None:
        return db[collection_name]
    return None

# -------------- Write Operations --------------
def create_patient(name: str, age: int, gender: str) -> str:
    """Creates a new patient record and returns the inserted patient_id as string."""
    col = get_collection("Patients")
    if col is None:
        return None
    
    patient_doc = {
        "name": name,
        "age": age,
        "gender": gender,
        "created_at": datetime.utcnow()
    }
    result = col.insert_one(patient_doc)
    return str(result.inserted_id)

def insert_patient_symptoms(patient_id: str, symptoms: list) -> bool:
    """Inserts reported symptoms for a specific patient_id."""
    col = get_collection("PatientSymptoms")
    if col is None or not symptoms:
        return False
    
    documents = []
    for symptom in symptoms:
        symptom_name = symptom.get("name")
        severity = symptom.get("severity", "Medium")
        if symptom_name:
            documents.append({
                "patient_id": patient_id,
                "symptom_name": symptom_name,
                "severity": severity,
                "reported_at": datetime.utcnow()
            })
    
    if documents:
        col.insert_many(documents)
        return True
    return False

def save_diagnosis_ranks(patient_id: str, ranked_diagnoses: list) -> bool:
    """Saves the prioritized list of diagnoses for a patient."""
    col = get_collection("DiagnosisRanks")
    if col is None or not ranked_diagnoses:
        return False
        
    documents = []
    for idx, diag in enumerate(ranked_diagnoses):
        documents.append({
            "patient_id": patient_id,
            "disease_name": diag.get("disease_name"),
            "confidence_score": diag.get("confidence_score"),
            "rank_position": idx + 1,
            "recorded_at": datetime.utcnow()
        })
        
    if documents:
        col.insert_many(documents)
        return True
    return False


# -------------- Read Operations --------------
def get_symptom_weights() -> list:
    """Fetches symptom weight definitions if available."""
    col = get_collection("SymptomWeights")
    if col is None:
        return []
    return list(col.find({}, {"_id": 0}))

def get_diagnostic_rules() -> list:
    """Fetches IF-THEN diagnostic rules."""
    col = get_collection("DiagnosticRules")
    if col is None:
        return []
    return list(col.find({}, {"_id": 0}))

def get_probability_table() -> list:
    """Fetches sensitivities and specificities for Bayesian probability."""
    col = get_collection("ProbabilityTable")
    if col is None:
        return []
    return list(col.find({}, {"_id": 0}))

def get_disease_details(disease_names: list) -> dict:
    """
    Fetches disease context (description, treatments).
    Returns a dictionary keyed by disease name.
    """
    col = get_collection("Diseases")
    if col is None or not disease_names:
        return {}
        
    cursor = col.find({"disease_name": {"$in": disease_names}}, {"_id": 0})
    result = {}
    for doc in cursor:
        name = doc.get("disease_name")
        if name:
            result[name] = doc
    return result

def get_available_symptoms_list() -> list:
    """Fetches a unique list of available symptoms from the DB."""
    # Try fetching from standard 'Symptoms' table first
    col = get_collection("Symptoms")
    if col is not None:
        symptoms = list(col.find({}, {"_id": 0, "symptom_name": 1}))
        if symptoms:
             return [s.get("symptom_name") for s in symptoms if "symptom_name" in s]
             
    # Fallback to weights table
    weights = get_symptom_weights()
    if weights:
        return list(set([w.get("symptom_name") for w in weights if "symptom_name" in w]))
        
    # Final fallback static list if DB is entirely empty
    return [
        "Fever", "Cough", "Fatigue", "Headache", "Nausea", 
        "Shortness of Breath", "Chest Pain", "Dizziness", "Sore Throat"
    ]
