import base64
import json
import re
import streamlit as st
from openai import OpenAI


EXTRACTION_PROMPT = """You are an expert document parser specialising in US death certificates.
Analyse this death certificate image and extract ALL available fields with high precision.

Return ONLY a valid JSON object with this exact structure:
{
  "state_detected": "<US state name or 'Unknown'>",
  "fields": {
    "deceased_name": "<full legal name>",
    "date_of_birth": "<MM/DD/YYYY or as shown>",
    "date_of_death": "<MM/DD/YYYY or as shown>",
    "ssn": "<XXX-XX-XXXX or 'Not visible'>",
    "address": "<last known address>",
    "cause_of_death": "<immediate cause>",
    "place_of_death": "<hospital/location name>",
    "next_of_kin": "<name of next of kin if present>",
    "certificate_number": "<certificate/document number>"
  },
  "confidence": {
    "deceased_name": <0.0-1.0>,
    "date_of_birth": <0.0-1.0>,
    "date_of_death": <0.0-1.0>,
    "ssn": <0.0-1.0>,
    "address": <0.0-1.0>,
    "cause_of_death": <0.0-1.0>,
    "place_of_death": <0.0-1.0>,
    "next_of_kin": <0.0-1.0>,
    "certificate_number": <0.0-1.0>
  },
  "format_notes": "<any notes about the certificate format or state-specific variations>"
}

Rules:
- Use "Not found" for fields not present or not legible
- Confidence 1.0 = clearly visible and certain, 0.0 = not found
- Confidence below 0.85 means the field needs human review
- Do NOT include any text outside the JSON object
"""


def get_client():
    """Initialise OpenAI client using Streamlit secrets."""
    return OpenAI(api_key=st.secrets["OPENAI_API_KEY"])


def extract_death_certificate(file_bytes: bytes, mime_type: str) -> dict:
    """
    Send image to GPT-4 Vision and extract structured death certificate data.
    Returns dict with fields, confidence scores, and state detection.
    """
    client = get_client()
    b64_image = base64.b64encode(file_bytes).decode("utf-8")

    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{b64_image}",
                                "detail": "high"
                            }
                        },
                        {
                            "type": "text",
                            "text": EXTRACTION_PROMPT
                        }
                    ]
                }
            ],
            max_tokens=1500,
            temperature=0.1
        )

        raw = response.choices[0].message.content.strip()
        raw = re.sub(r"^```json\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)

        return json.loads(raw)

    except json.JSONDecodeError as e:
        return {"error": f"Failed to parse GPT-4 response as JSON: {str(e)}"}
    except Exception as e:
        return {"error": str(e)}