import streamlit as st
import json

st.title("🔧 Secret Debugger")

# Check 1: API Key
if "GOOGLE_API_KEY" in st.secrets:
    st.success("✅ GOOGLE_API_KEY found")
else:
    st.error("❌ GOOGLE_API_KEY is missing in Secrets")

# Check 2: Folder ID
if "DRIVE_FOLDER_ID" in st.secrets:
    st.success("✅ DRIVE_FOLDER_ID found")
else:
    st.error("❌ DRIVE_FOLDER_ID is missing in Secrets")

# Check 3: JSON Content
if "GCP_JSON" in st.secrets:
    st.success("✅ GCP_JSON key found")
    try:
        # Try to read it as JSON
        info = json.loads(st.secrets["GCP_JSON"])
        st.success("✅ GCP_JSON is valid JSON format!")
        st.write(f"Project ID detected: {info.get('project_id', 'Unknown')}")
    except Exception as e:
        st.error(f"❌ GCP_JSON exists but is INVALID. Error: {e}")
        st.warning("Tip: Make sure you wrapped the JSON in triple quotes \"\"\" in the Secrets box.")
else:
    st.error("❌ GCP_JSON key is missing in Secrets")
