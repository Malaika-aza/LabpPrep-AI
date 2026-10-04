import streamlit as st
from datetime import date, time
from google import genai

st.set_page_config(
    page_title="LabPrep AI",
    page_icon="🧪",
    layout="wide",
)

# -------------------------------------------------------------------
# LABPREP AI
# MVP for patient preparation and pre-analytical safety.
#
# IMPORTANT:
# The rules below are demo data. Before real clinical use, replace them
# with your laboratory's approved SOP and verify every requirement.
# -------------------------------------------------------------------

TESTS = {
    "CBC / Complete Blood Count": {
        "sample": "Whole blood",
        "tube": "EDTA tube (commonly lavender/purple top)",
        "fasting": "Usually not required for CBC alone.",
        "preparation": [
            "Normal meals are usually acceptable unless your clinician/lab says otherwise.",
            "Follow any special instructions written on the test order.",
        ],
        "staff_checks": [
            "Confirm patient identity and test request.",
            "Use the laboratory-approved EDTA tube.",
            "Check required fill volume and specimen acceptance criteria in the SOP.",
            "Label the specimen according to laboratory policy.",
        ],
        "note": "Tube type, volume, handling and rejection criteria must be confirmed against the performing laboratory SOP.",
    },
    "Fasting Blood Glucose": {
        "sample": "Plasma/serum depending on the laboratory method",
        "tube": "Use the tube/additive specified by the performing laboratory's glucose SOP.",
        "fasting": "Fasting may be required; follow the exact duration given by the laboratory/clinician.",
        "preparation": [
            "Follow the fasting instructions supplied by the laboratory or clinician.",
            "Do not stop or change prescribed medicines unless your clinician tells you to.",
            "Ask the laboratory whether water is permitted during the fasting period.",
        ],
        "staff_checks": [
            "Confirm the requested glucose test and preparation status.",
            "Use the laboratory-approved tube/additive for the analyzer/method.",
            "Check collection volume, labeling, handling and transport requirements.",
        ],
        "note": "Glucose tube requirements can vary by method. Verify the current local SOP.",
    },
    "Lipid Profile": {
        "sample": "Serum or plasma depending on the laboratory method",
        "tube": "Use the tube/additive specified by the performing laboratory's lipid-profile SOP.",
        "fasting": "Fasting requirements vary according to the laboratory and clinical purpose.",
        "preparation": [
            "Follow the fasting instructions given by your laboratory or clinician.",
            "Do not change prescribed medicines unless instructed by your clinician.",
        ],
        "staff_checks": [
            "Confirm whether fasting is required for the requested panel.",
            "Use the laboratory-approved specimen tube.",
            "Check labeling, volume, handling and transport requirements.",
        ],
        "note": "Verify current local requirements before collection.",
    },
    "HbA1c": {
        "sample": "Whole blood",
        "tube": "EDTA tube is commonly used; verify the analyzer/laboratory SOP.",
        "fasting": "Usually not required.",
        "preparation": [
            "Normal food and water are usually acceptable for HbA1c alone.",
            "Follow any additional instructions from your clinician.",
        ],
        "staff_checks": [
            "Confirm the test request and patient identity.",
            "Use the laboratory-approved EDTA tube.",
            "Check minimum volume and sample stability requirements in the SOP.",
        ],
        "note": "Tube, volume and stability requirements vary by laboratory/analyzer.",
    },
    "PT / INR": {
        "sample": "Citrated plasma",
        "tube": "Sodium citrate tube (commonly light blue top)",
        "fasting": "Usually not required unless another ordered test requires fasting.",
        "preparation": [
            "Tell the laboratory about relevant medicines and instructions from your clinician.",
            "Do not stop or change anticoagulant medicines unless your clinician instructs you to.",
        ],
        "staff_checks": [
            "Use the laboratory-approved sodium citrate tube.",
            "Fill the tube to the required level so the blood-to-anticoagulant ratio is correct.",
            "Check specimen labeling, collection conditions and rejection criteria in the SOP.",
        ],
        "note": "Correct fill volume and blood-to-anticoagulant ratio are important. Follow the local SOP.",
    },
    "Liver Function Tests (LFT)": {
        "sample": "Serum or plasma depending on the laboratory method",
        "tube": "Use the tube/additive specified by the performing laboratory's LFT SOP.",
        "fasting": "Fasting may be requested when LFTs are ordered with other fasting tests; follow your lab/clinician.",
        "preparation": [
            "Follow the specific preparation instructions supplied with the test order.",
            "Do not stop medicines unless your clinician tells you to.",
        ],
        "staff_checks": [
            "Confirm the ordered tests and preparation requirements.",
            "Use the laboratory-approved tube.",
            "Check volume, labeling, processing and transport requirements.",
        ],
        "note": "Exact tube/additive requirements vary by laboratory and analyzer.",
    },
    "Urinalysis": {
        "sample": "Urine",
        "tube": "Clean, leak-proof urine container approved by the laboratory.",
        "fasting": "Usually not required.",
        "preparation": [
            "Use the collection method and timing specified by your laboratory.",
            "Follow the laboratory's instructions to reduce contamination.",
        ],
        "staff_checks": [
            "Provide the laboratory-approved urine container.",
            "Confirm the requested urine test and collection method.",
            "Check labeling, volume, transport time and storage requirements.",
        ],
        "note": "Container and collection instructions should follow the laboratory SOP.",
    },
}

ALIASES = {
    "cbc": "CBC / Complete Blood Count",
    "fbc": "CBC / Complete Blood Count",
    "complete blood count": "CBC / Complete Blood Count",
    "fbs": "Fasting Blood Glucose",
    "fasting glucose": "Fasting Blood Glucose",
    "fasting blood sugar": "Fasting Blood Glucose",
    "hba1c": "HbA1c",
    "a1c": "HbA1c",
    "inr": "PT / INR",
    "pt inr": "PT / INR",
    "lft": "Liver Function Tests (LFT)",
    "urinalysis": "Urinalysis",
    "urine routine": "Urinalysis",
}


def normalize_test_name(name: str):
    value = " ".join(name.strip().lower().split())

    if value in ALIASES:
        return ALIASES[value]

    for test in TESTS:
        if value == test.lower():
            return test

    for alias, test in ALIASES.items():
        if alias in value:
            return test

    for test in TESTS:
        if test.lower() in value:
            return test

    return None


def get_api_key():
    try:
        return st.secrets.get("GEMINI_API_KEY", "")
    except Exception:
        return ""


def generate_patient_explanation(test_name: str, info: dict, language: str):
    api_key = get_api_key()

    if not api_key:
        return None, "Gemini API key is not configured. The verified guide is still available."

    language_rule = (
        "Use very simple Roman Urdu mixed with simple English."
        if language == "Urdu + English"
        else "Use very simple English."
    )

    prompt = f"""
You are the patient-education assistant in LabPrep AI.

{language_rule}

The app has a verified laboratory knowledge base. You MUST use only the
information provided below. Never invent a tube, fasting duration, sample
type, minimum volume, medicine instruction, or collection requirement.

TEST:
{test_name}

VERIFIED INFORMATION:
Sample: {info["sample"]}
Tube/container: {info["tube"]}
Fasting: {info["fasting"]}

Patient preparation:
{chr(10).join("- " + x for x in info["preparation"])}

Safety note:
{info["note"]}

Write a short patient-friendly guide with these headings:
### What is this test?
Give only a general, non-diagnostic explanation.

### Before the test
Give the preparation points above in easy language.

### Sample
Explain what sample is collected and repeat the verified tube/container
information.

### Important
Tell the patient to follow their laboratory/clinician instructions if
they differ. Never advise stopping medication.

Do not diagnose, predict results, or give treatment advice.
"""

    try:
        client = genai.Client(api_key=api_key)

        response = client.models.generate_content(
            model="gemini-2.5-flash",",
            contents=prompt,
        )

        text = (response.text or "").strip()

        if not text:
            return None, "Gemini returned an empty response. Showing the verified guide instead."

        return text, None

    except Exception as exc:
        return None, f"Gemini could not generate the explanation: {exc}"


# -------------------------------------------------------------------
# UI
# -------------------------------------------------------------------

st.title("🧪 LabPrep AI")
st.caption(
    "Patient preparation + laboratory pre-analytical safety assistant"
)

st.warning(
    "MVP / educational prototype: verify all sample, tube, volume, "
    "transport, storage and preparation requirements against your "
    "laboratory's current SOP before clinical use."
)

patient_tab, staff_tab, reminder_tab = st.tabs(
    ["👤 Patient Guide", "🔬 Lab Staff", "⏰ Reminder"]
)

with patient_tab:
    st.header("Prepare for your laboratory test")

    test_input = st.text_input(
        "Enter test name",
        placeholder="Example: CBC, HbA1c, PT/INR, Fasting Blood Glucose",
    )

    language = st.selectbox(
        "Guide language",
        ["Urdu + English", "English"],
    )

    if st.button("Generate Preparation Guide", type="primary"):
        if not test_input.strip():
            st.error("Please enter a test name.")
        else:
            test_name = normalize_test_name(test_input)

            if not test_name:
                st.error(
                    "This test is not available in the verified database."
                )
                st.info(
                    "Please confirm preparation requirements with the "
                    "performing laboratory instead of using a guessed requirement."
                )
            else:
                info = TESTS[test_name]

                st.success(f"Test identified: {test_name}")

                st.subheader("Quick verified information")
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown(f"**Sample:** {info['sample']}")
                    st.markdown(f"**Tube/container:** {info['tube']}")

                with col2:
                    st.markdown(f"**Fasting:** {info['fasting']}")

                st.markdown("**Preparation:**")
                for item in info["preparation"]:
                    st.markdown(f"- {item}")

                explanation, error_message = generate_patient_explanation(
                    test_name,
                    info,
                    language,
                )

                if explanation:
                    st.subheader("🤖 Simple AI explanation")
                    st.markdown(explanation)

                if error_message:
                    st.info(error_message)

with staff_tab:
    st.header("Laboratory staff checklist")

    staff_test = st.selectbox(
        "Select test",
        list(TESTS.keys()),
    )

    info = TESTS[staff_test]

    st.subheader(staff_test)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### Specimen")
        st.write(info["sample"])

    with col2:
        st.markdown("### Tube / container")
        st.write(info["tube"])

    st.markdown("### Pre-laboratory requirements")

    for item in info["preparation"]:
        st.markdown(f"- {item}")

    st.markdown("### Pre-analytical checklist")

    for item in info["staff_checks"]:
        st.checkbox(item, key=f"{staff_test}-{item}")

    st.info(
        "The checklist is a support tool, not a replacement for your "
        "laboratory SOP. Confirm collection order, tube/additive, fill "
        "volume, labeling, processing, transport, storage and rejection "
        "criteria locally."
    )

with reminder_tab:
    st.header("Patient reminder planner")

    st.write(
        "This MVP creates a reminder plan in the app. Actual SMS, "
        "WhatsApp or email delivery requires a separate approved "
        "notification service."
    )

    reminder_test = st.text_input(
        "Test name",
        placeholder="Example: CBC",
    )

    reminder_date = st.date_input(
        "Test date",
        min_value=date.today(),
    )

    reminder_time = st.time_input(
        "Reminder time",
        value=time(18, 0),
    )

    if st.button("Create Reminder Plan"):
        if not reminder_test.strip():
            st.error("Please enter the test name.")
        else:
            test_name = normalize_test_name(reminder_test)

            if test_name:
                display_name = test_name
            else:
                display_name = reminder_test.strip()

            st.success("Reminder plan created.")

            st.markdown(
                f"""
**Test:** {display_name}

**Date:** {reminder_date.strftime("%d %B %Y")}

**Time:** {reminder_time.strftime("%I:%M %p")}

**Reminder message:**

Please review your laboratory's preparation instructions before your
test. If you are unsure about fasting, medicines, sample collection,
or any other requirement, contact the laboratory or your clinician.
"""
            )

st.divider()

st.caption(
    "LabPrep AI • Prototype • Not a diagnostic tool • "
    "Always follow the performing laboratory's SOP."
)
