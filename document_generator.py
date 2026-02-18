import streamlit as st
from openai import OpenAI
from datetime import date


INSTITUTION_CONFIGS = {
    "Social Security Administration": {
        "ref": "SSA Form SSA-721",
        "address": "Social Security Administration\nP.O. Box 33003\nBaltimore, MD 21290-3003",
        "purpose": "notification of death to stop benefit payments and initiate survivor benefits review",
        "tone": "formal government",
        "key_fields": ["deceased_name", "ssn", "date_of_death", "date_of_birth", "next_of_kin"]
    },
    "Medicare/Medicaid": {
        "ref": "CMS Death Notification",
        "address": "Centers for Medicare & Medicaid Services\n7500 Security Boulevard\nBaltimore, MD 21244",
        "purpose": "notification of death to terminate Medicare/Medicaid coverage",
        "tone": "formal government",
        "key_fields": ["deceased_name", "ssn", "date_of_death", "date_of_birth"]
    },
    "IRS": {
        "ref": "IRS Final Return Notification",
        "address": "Internal Revenue Service\nCincinnati, OH 45999",
        "purpose": "notification of death for tax record purposes and to authorise estate representative",
        "tone": "formal legal",
        "key_fields": ["deceased_name", "ssn", "date_of_death", "address", "next_of_kin"]
    },
    "Bank/Financial": {
        "ref": "Account Closure / Estate Administration Request",
        "address": "[Bank Name and Branch Address]",
        "purpose": "notification of account holder death and initiation of estate administration process",
        "tone": "formal professional",
        "key_fields": ["deceased_name", "date_of_death", "address", "next_of_kin", "certificate_number"]
    },
    "Insurance Company": {
        "ref": "Death Claim Notification",
        "address": "[Insurance Company Name]\n[Claims Department Address]",
        "purpose": "formal death notification to initiate life insurance claim process",
        "tone": "formal professional",
        "key_fields": ["deceased_name", "date_of_death", "date_of_birth", "ssn", "cause_of_death", "certificate_number"]
    },
    "DMV": {
        "ref": "Driver Licence Cancellation Notice",
        "address": "[State] Department of Motor Vehicles\n[DMV Address]",
        "purpose": "notification of death to cancel driving licence and vehicle registration",
        "tone": "formal government",
        "key_fields": ["deceased_name", "date_of_death", "date_of_birth", "address"]
    },
    "Utilities": {
        "ref": "Account Holder Death Notification",
        "address": "[Utility Provider Name]\nCustomer Services Department",
        "purpose": "notification of account holder death to transfer or close utility accounts",
        "tone": "professional",
        "key_fields": ["deceased_name", "date_of_death", "address", "next_of_kin"]
    }
}

LETTER_PROMPT = """You are a professional legal document writer specialising in estate administration correspondence.

Generate a complete, professional legal letter for the following:

Institution: {institution}
Reference: {ref}
Purpose: {purpose}
Tone: {tone}
Today's Date: {today}

Deceased Person's Information:
{fields_text}

Requirements:
- Write a complete, ready-to-send formal letter
- Include proper salutation, body paragraphs, and closing
- Do NOT make it look AI-generated — use natural, human legal writing style
- Include reference to the enclosed certified copy of the death certificate
- Request specific next steps from the institution
- Keep to 300-400 words
- Format with proper letter structure (date, address block, re: line, body, closing)
- Do not include placeholder brackets except for [Your Name], [Your Signature], [Account Number if known]

Return ONLY the letter text, no explanations."""


def get_client():
    """Initialise OpenAI client using Streamlit secrets."""
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def generate_legal_letter(fields: dict, institution: str) -> dict:
    """
    Generate a professional institution-specific legal letter using GPT-4.
    """
    client = get_client()
    config = INSTITUTION_CONFIGS.get(institution, INSTITUTION_CONFIGS["Bank/Financial"])

    field_labels = {
        "deceased_name": "Full Name",
        "date_of_birth": "Date of Birth",
        "date_of_death": "Date of Death",
        "ssn": "Social Security Number",
        "address": "Last Known Address",
        "cause_of_death": "Cause of Death",
        "place_of_death": "Place of Death",
        "next_of_kin": "Next of Kin / Estate Representative",
        "certificate_number": "Death Certificate Number",
    }

    fields_text = "\n".join([
        f"- {field_labels.get(k, k)}: {v}"
        for k, v in fields.items()
        if v and v not in ["Not found", "Not visible", ""]
    ])

    prompt = LETTER_PROMPT.format(
        institution=institution,
        ref=config["ref"],
        purpose=config["purpose"],
        tone=config["tone"],
        today=date.today().strftime("%B %d, %Y"),
        fields_text=fields_text
    )

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1000,
            temperature=0.4
        )

        return {
            "content": response.choices[0].message.content.strip(),
            "institution": institution,
            "ref": config["ref"]
        }

    except Exception as e:
        return {"error": str(e)}