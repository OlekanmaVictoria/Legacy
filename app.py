import streamlit as st
import json
from PIL import Image

from extractor import extract_death_certificate
from document_generator import generate_legal_letter

st.set_page_config(
    page_title="Legacy AI",
    page_icon="🕊️",
    layout="wide"
)

# --- Styling ---
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        padding: 2rem;
        border-radius: 12px;
        margin-bottom: 2rem;
        color: white;
    }
    .step-badge {
        background: #0f3460;
        color: white;
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: bold;
        margin-bottom: 0.5rem;
        display: inline-block;
    }
    .result-card {
        background: #f8f9fa;
        border: 1px solid #e0e0e0;
        border-left: 4px solid #0f3460;
        border-radius: 8px;
        padding: 1.2rem;
        margin-bottom: 1rem;
    }
    .confidence-high { color: #2e7d32; font-weight: bold; }
    .confidence-low { color: #c62828; font-weight: bold; }
    .stButton>button {
        background: #0f3460;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.6rem 2rem;
        font-weight: bold;
        width: 100%;
    }
    .stButton>button:hover { background: #16213e; }
</style>
""", unsafe_allow_html=True)

# --- Header ---
st.markdown("""
<div class="main-header">
    <h1 style="margin:0; font-size:2rem;">🕊️ Legacy AI</h1>
    <p style="margin:0.5rem 0 0; opacity:0.8;">
        Handling the paperwork. So you don't have to.
    </p>
</div>
""", unsafe_allow_html=True)

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🕊️ Legacy AI")
    st.markdown("Compassionate administration for life's hardest moment.")
    st.markdown("---")
    st.markdown("### 📋 How it works")
    st.markdown("""
1. **Upload** a death certificate (image)
2. **GPT-4 Vision** extracts all key fields
3. **Review** and edit the extracted data
4. **Generate** institution-specific legal letters
5. **Download** your documents
    """)
    st.markdown("---")
    st.markdown("**Select Institution**")
    institutions = [
        "Social Security Administration",
        "Medicare/Medicaid",
        "IRS",
        "Bank/Financial",
        "Insurance Company",
        "DMV",
        "Utilities"
    ]
    selected_inst = st.selectbox("Institution template", institutions)

# --- Main UI ---
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.markdown('<div class="step-badge">STEP 1 — UPLOAD</div>', unsafe_allow_html=True)
    st.markdown("### Upload Death Certificate")

    uploaded_file = st.file_uploader(
        "Drag & drop or browse",
        type=["png", "jpg", "jpeg"],
        help="Supports all 50 US state formats"
    )

    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Certificate", use_container_width=True)

        st.markdown("---")
        st.markdown('<div class="step-badge">STEP 2 — EXTRACT</div>', unsafe_allow_html=True)
        st.markdown("### Extract Certificate Data")

        if st.button("🔍 Extract with GPT-4 Vision"):
            with st.spinner("GPT-4 Vision is analysing the certificate..."):
                file_bytes = uploaded_file.getvalue()
                result = extract_death_certificate(file_bytes, uploaded_file.type)

            if "error" in result:
                st.error(f"Extraction failed: {result['error']}")
            else:
                st.session_state["extracted"] = result
                st.success("✅ Extraction complete!")

with col2:
    st.markdown('<div class="step-badge">STEP 3 — REVIEW</div>', unsafe_allow_html=True)
    st.markdown("### Extracted Data")

    if "extracted" in st.session_state:
        data = st.session_state["extracted"]
        fields = data.get("fields", {})
        confidences = data.get("confidence", {})
        state_detected = data.get("state_detected", "Unknown")

        st.markdown(f"**State Format Detected:** `{state_detected}`")
        st.markdown("---")

        edited = {}
        field_labels = {
            "deceased_name": "Full Name",
            "date_of_birth": "Date of Birth",
            "date_of_death": "Date of Death",
            "ssn": "Social Security Number",
            "address": "Last Known Address",
            "cause_of_death": "Cause of Death",
            "place_of_death": "Place of Death",
            "next_of_kin": "Next of Kin",
            "certificate_number": "Certificate Number",
        }

        for key, label in field_labels.items():
            val = fields.get(key, "")
            conf = confidences.get(key, 1.0)
            conf_label = (
                "<span class='confidence-high'>✓ High</span>"
                if conf >= 0.85
                else f"<span class='confidence-low'>⚠ Low ({int(conf*100)}%)</span>"
            )
            st.markdown(f"**{label}** {conf_label}", unsafe_allow_html=True)
            edited[key] = st.text_input(label, value=val, label_visibility="collapsed", key=f"field_{key}")

        st.session_state["edited_fields"] = edited

        with st.expander("📦 View Raw JSON"):
            st.json({"fields": edited, "confidence": confidences, "state_detected": state_detected})

        st.markdown("---")
        st.markdown('<div class="step-badge">STEP 4 — GENERATE</div>', unsafe_allow_html=True)
        st.markdown("### Generate Legal Letter")
        st.markdown(f"**Template:** {selected_inst}")

        if st.button("📝 Generate Legal Document"):
            with st.spinner("Generating professional legal letter..."):
                letter = generate_legal_letter(edited, selected_inst)

            if "error" in letter:
                st.error(letter["error"])
            else:
                st.session_state["letter"] = letter
                st.success("✅ Document generated!")

    else:
        st.markdown("""
<div style="text-align:center; padding: 4rem 1rem; color: #999;">
    <div style="font-size: 4rem;">📋</div>
    <p>Upload a certificate and run extraction<br>to see results here.</p>
</div>
        """, unsafe_allow_html=True)

# --- Document Output ---
if "letter" in st.session_state:
    st.markdown("---")
    st.markdown('<div class="step-badge">STEP 5 — DOWNLOAD</div>', unsafe_allow_html=True)
    st.markdown("### Generated Legal Document")

    letter = st.session_state["letter"]
    col_preview, col_download = st.columns([2, 1])

    with col_preview:
        st.markdown('<div class="result-card">', unsafe_allow_html=True)
        st.text(letter["content"])
        st.markdown('</div>', unsafe_allow_html=True)

    with col_download:
        st.markdown("#### Download Options")

        st.download_button(
            label="⬇️ Download as .txt",
            data=letter["content"],
            file_name=f"legacy_{selected_inst.replace('/', '_').replace(' ', '_')}.txt",
            mime="text/plain"
        )

        json_data = json.dumps({
            "institution": selected_inst,
            "extracted_fields": st.session_state.get("edited_fields", {}),
            "letter": letter["content"]
        }, indent=2)

        st.download_button(
            label="⬇️ Download JSON Bundle",
            data=json_data,
            file_name="legacy_bundle.json",
            mime="application/json"
        )

        st.markdown("---")
        st.markdown("**Document Info**")
        st.markdown(f"- Institution: `{selected_inst}`")
        st.markdown(f"- State: `{st.session_state['extracted'].get('state_detected', 'N/A')}`")
        st.markdown(f"- Fields extracted: `{len(st.session_state.get('edited_fields', {}))}`")