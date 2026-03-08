-- ==========================================
-- MODULE 12: RULE-BASED DISEASE RANKING SYSTEM
-- Author: Chamalla Bhanu Prakash (24JE0603)
-- Note: References Patient (M1), Disease (M7), and Symptom (M7) tables.
-- ==========================================

-- 1. IF-THEN Diagnostic Rules Table
CREATE TABLE Diagnostic_rule (
    rule_id INT PRIMARY KEY,
    disease_id INT, 
    rule_condition VARCHAR(255) NOT NULL,
    rule_type VARCHAR(50),
    FOREIGN KEY (disease_id) REFERENCES Disease(disease_id)
);

-- 2. Bayesian Probability Table (Math Engine)
CREATE TABLE Probability_table (
    prob_id INT PRIMARY KEY,
    disease_id INT,
    symptom_id INT,
    sensitivity DECIMAL(5,4),
    specificity DECIMAL(5,4),
    likelihood_ratio DECIMAL(5,2),
    FOREIGN KEY (disease_id) REFERENCES Disease(disease_id),
    FOREIGN KEY (symptom_id) REFERENCES Symptom(symptom_id)
);

-- 3. Symptom Severity Weights (The Triage Prep)
CREATE TABLE Symptom_weight (
    weight_id INT PRIMARY KEY,
    symptom_id INT,
    weight_value INT NOT NULL CHECK (weight_value BETWEEN 1 AND 10),
    FOREIGN KEY (symptom_id) REFERENCES Symptom(symptom_id)
);

-- 4. Final Diagnosis Ranking (The Output)
CREATE TABLE Diagnosis_Rank (
    rank_id INT PRIMARY KEY,
    patient_id INT,
    disease_id INT,
    rank_position INT NOT NULL,
    confidence_score DECIMAL(5,2) NOT NULL,
    FOREIGN KEY (patient_id) REFERENCES Patient(patient_id),
    FOREIGN KEY (disease_id) REFERENCES Disease(disease_id)
);