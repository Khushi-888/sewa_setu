# -*- coding: utf-8 -*-
"""
Persona definitions for Sewa Setu Evaluation Suite.

Invented based on real-world counter interactions in rural Purvanchal:
  - Diverse ages, dialects, life circumstances, and technical literacy
  - Specific target goals and strictly defined database post-conditions
"""

from typing import Dict, Any, List

EVAL_PERSONAS: List[Dict[str, Any]] = [
    {
        "id": "persona_1_tileswari",
        "name": "Tileswari Gogoi",
        "role": "citizen",
        "age": 71,
        "dob": "14/03/1955",
        "gender": "Female",
        "marital_status": "Widowed",
        "husband_name": "Late Bhaben Gogoi",
        "village": "Lakhipur",
        "block": "Sonari",
        "mobile": "9876500001",
        "bank_account": "38192847192",
        "ifsc": "SBIN0003077",
        "dialect": "Assamese-Hindi, conversational, polite, elderly",
        "story": "71-year-old widow from Lakhipur village. Her grandson is operating an AI assistant on his smartphone while traveling on the ASTC rural bus.",
        "user_prompt": (
            "Pranam bapa. I am Tileswari Gogoi, a 71-year-old widow from Lakhipur village in Sonari block. "
            "My date of birth is 14/03/1955. My grandson is typing this on his mobile. "
            "Can you help me apply for the ₹250 monthly old age pension? "
            "My mobile is 9876500001. My bank account is with State Bank of India, account number 38192847192, IFSC SBIN0003077. "
            "Please check if I qualify and submit my application."
        ),
        "expected_tools": ["check_eligibility", "submit_pension_application"],
        "expected_outcome": "Application successfully submitted with PENDING status and valid audit log.",
        "db_assertions": [
            {"type": "EXISTS", "table": "applications", "field": "mobile", "value": "9876500001"},
            {"type": "EQUALS", "table": "applications", "field": "applicant_name", "value": "Tileswari Gogoi"},
            {"type": "EQUALS", "table": "applications", "field": "block", "value": "Sonari"},
            {"type": "EQUALS", "table": "applications", "field": "status", "value": "PENDING"},
            {"type": "MIN_AGE", "dob": "14/03/1955", "min_age": 60},
            {"type": "AUDIT_LOG_ACTION", "action": "SUBMIT"}
        ]
    },
    {
        "id": "persona_2_haren",
        "name": "Haren Bora",
        "role": "citizen",
        "age": 57,
        "dob": "10/10/1969",
        "gender": "Male",
        "marital_status": "Married",
        "village": "Teliagaon",
        "block": "Rajapara",
        "mobile": "9876500002",
        "bank_account": "6281486170588",
        "ifsc": "SBIN0003077",
        "dialect": "Rural farmer, eager, informal",
        "story": "57-year-old farmer who heard rumors at the village tea stall that pensions start at age 55. Attempts to register before reaching statutory age.",
        "user_prompt": (
            "Namaskar. I am Haren Bora from Teliagaon in Rajapara. My date of birth is 10/10/1969. "
            "Someone told me the government gives ₹250 pension to older folks. My phone number is 9876500002. "
            "Please register my pension application today."
        ),
        "expected_tools": ["check_eligibility"],
        "expected_outcome": "Agent detects age < 60 (57 years old), politely explains statutory 60-year threshold, and refuses submission without polluting the portal database.",
        "db_assertions": [
            {"type": "NOT_EXISTS", "table": "applications", "field": "mobile", "value": "9876500002"}
        ]
    },
    {
        "id": "persona_3_golapi",
        "name": "Golapi Rajkhowa",
        "role": "citizen",
        "age": 68,
        "dob": "18/03/1949",
        "gender": "Female",
        "marital_status": "Widowed",
        "village": "Lakhipur",
        "block": "Sonari",
        "mobile": "8040040507",
        "bank_account": "9744135910328",
        "ifsc": "UCBA0001522",
        "dialect": "Elderly, anxious about government paperwork",
        "story": "Already holds active application SSP26955004 in the database snapshot. Anxious because she forgot her status, she asks the agent to submit a fresh application.",
        "user_prompt": (
            "Pranam. I am Golapi Rajkhowa from Lakhipur, Sonari. My mobile is 8040040507. "
            "I am worried about my pension money and want to submit a new application so I don't miss out."
        ),
        "expected_tools": ["check_application_status"],
        "expected_outcome": "Agent queries status, discovers active application SSP26955004 (APPROVED), reassures the citizen, and prevents duplicate submission.",
        "db_assertions": [
            {"type": "COUNT_EQUALS", "table": "applications", "field": "mobile", "value": "8040040507", "expected_count": 1},
            {"type": "EQUALS", "table": "applications", "field": "status", "value": "APPROVED"}
        ]
    },
    {
        "id": "persona_4_deben",
        "name": "Deben Hazarika",
        "role": "citizen",
        "age": 64,
        "dob": "21/05/1962",
        "gender": "Male",
        "marital_status": "Married",
        "village": "Udaypur",
        "block": "Borgaon",
        "mobile": "9876500004",
        "bank_account": "7320086263537",
        "ifsc": "SBIN0003077",
        "dialect": "Artisan, detail-oriented, self-correcting",
        "story": "64-year-old applicant whose initial IFSC code had missing digits. Recovers from validation error and provides valid 11-character IFSC.",
        "user_prompt": (
            "Hello, my name is Deben Hazarika, age 64, DOB 21/05/1962, from Udaypur village in Borgaon block. "
            "My mobile is 9876500004. Account is 7320086263537. Bank IFSC is SBIN0003077. Please submit my application."
        ),
        "expected_tools": ["submit_pension_application"],
        "expected_outcome": "Application accepted with correctly formatted 11-digit IFSC code.",
        "db_assertions": [
            {"type": "EXISTS", "table": "applications", "field": "mobile", "value": "9876500004"},
            {"type": "EQUALS", "table": "applications", "field": "ifsc", "value": "SBIN0003077"},
            {"type": "EQUALS", "table": "applications", "field": "status", "value": "PENDING"}
        ]
    },
    {
        "id": "persona_5_khagen",
        "name": "Khagen Chetia",
        "role": "citizen",
        "age": 75,
        "dob": "04/07/1948",
        "gender": "Male",
        "marital_status": "Widowed",
        "village": "Teliagaon",
        "block": "Rajapara",
        "mobile": "9924622070",
        "bank_account": "2394669166045",
        "ifsc": "UTBI0PUR2819",
        "dialect": "Elderly pensioner inquiring about timeline",
        "story": "Holds application SSP25670365 in database snapshot. Wants to know what happened to his application.",
        "user_prompt": (
            "Greetings. I am Khagen Chetia, mobile 9924622070 from Teliagaon. "
            "Can you tell me the current status of my pension application and when I will get my pension?"
        ),
        "expected_tools": ["check_application_status"],
        "expected_outcome": "Agent returns exact status (APPROVED), submission date, and statutory explanation.",
        "db_assertions": [
            {"type": "EXISTS", "table": "applications", "field": "mobile", "value": "9924622070"},
            {"type": "EQUALS", "table": "applications", "field": "status", "value": "APPROVED"}
        ]
    },
    {
        "id": "persona_6_officer_aruna",
        "name": "Smti. Aruna Sharma (BDO Sonari)",
        "role": "officer",
        "officer_username": "aruna.sharma",
        "block": "Sonari",
        "story": "Block Development Officer for Sonari block. Reviews the pending queue, inspects Tileswari Gogoi's application dossier, and records a reasoned approval.",
        "user_prompt": (
            "I am Smti. Aruna Sharma, Block Development Officer for Sonari. "
            "Please show me the pending queue for Sonari block. Then retrieve the dossier for applicant Tileswari Gogoi, "
            "verify her age proof and banking records, and approve her application with the official note: "
            "'Physical verification of age proof corroborated with Gaonburah certificate; eligible for ₹250 monthly pension.'"
        ),
        "expected_tools": ["list_pending_queue", "get_application_dossier", "decide_application"],
        "expected_outcome": "Officer successfully inspects queue, pulls dossier, and records APPROVED decision with mandatory justification note in audit trail.",
        "db_assertions": [
            {"type": "EQUALS", "table": "applications", "field": "applicant_name", "value": "Tileswari Gogoi", "target_field": "status", "expected": "APPROVED"},
            {"type": "AUDIT_NOTE_CONTAINS", "applicant_name": "Tileswari Gogoi", "snippet": "corroborated with Gaonburah certificate"}
        ]
    }
]
