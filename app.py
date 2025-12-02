import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os
import uuid
import datetime
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Rainbow Form Portal", page_icon="🎨", layout="wide")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .stApp {background-color: #f8f9fa;}
    div[data-testid="column"] {
        background-color: white;
        padding: 20px;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border: 1px solid #eee;
    }
    .price-tag {
        font-size: 1.2em;
        font-weight: bold;
        color: #d32f2f;
        margin-bottom: 10px;
    }
    .original-price {
        text-decoration: line-through;
        color: #757575;
        font-size: 0.8em;
        margin-right: 5px;
    }
    div.stButton > button {
        width: 100%;
        border-radius: 8px;
        font-weight: bold;
        height: 50px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURE SETUP (API + DRIVE) ---
try:
    # Gemini Key
    api_key = st.secrets["GOOGLE_API_KEY"]
    
    # Drive Folder ID
    folder_id = st.secrets["DRIVE_FOLDER_ID"]
    
    # Drive Credentials (NEW METHOD: Reads the table from secrets)
    # Convert the Streamlit Secrets object into a standard Python dictionary
    gcp_info = dict(st.secrets["gcp_service_account"])
    
    # Authenticate with Google Drive
    creds = service_account.Credentials.from_service_account_info(gcp_info)

except Exception as e:
    st.error(f"⚠️ Server Error: Secret Configuration Issue. {e}")
    st.stop()

# --- DRIVE UPLOAD FUNCTION ---
def upload_to_drive(file_bytes, file_name, mime_type):
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': file_name, 'parents': [folder_id]}
        media = MediaIoBaseUpload(io.BytesIO(file_bytes), mimetype=mime_type)
        file = service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        return file.get('id')
    except Exception as e:
        print(f"Drive Upload Error: {e}")
        return None

# --- 3. LOAD LOGO ---
logo_data = None
if os.path.exists("logo.png"):
    try:
        pil_logo = Image.open("logo.png")
        img_byte_arr = io.BytesIO()
        pil_logo.save(img_byte_arr, format=pil_logo.format if pil_logo.format else 'PNG')
        logo_data = {'mime_type': 'image/png', 'data': img_byte_arr.getvalue()}
    except:
        pass

# --- 4. SESSION STATE ---
if 'user_email' not in st.session_state:
    st.session_state.user_email = None
if 'credits' not in st.session_state:
    st.session_state.credits = 3
if 'generated_images' not in st.session_state:
    st.session_state.generated_images = None
if 'current_design_id' not in st.session_state:
    st.session_state.current_design_id = None

# --- 5. LOGIN GATEKEEPER ---
if not st.session_state.user_email:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        if logo_data:
            st.image("logo.png", width=300)
        else:
            st.title("Rainbow Form")
            
        st.markdown("### 👋 Welcome to the Toy Factory!")
        st.write("Enter your email to unlock your **3 Free 3D Designs**.")
        email_input = st.text_input("Email Address", placeholder="mom@example.com")
        if st.button("🔓 Unlock Free Tries"):
            if "@" in email_input and "." in email_input:
                st.session_state.user_email = email_input
                st.rerun()
            else:
                st.error("Please enter a valid email address.")
    st.stop()

# --- 6. MAIN TOOL ---
if logo_data:
    st.image("logo.png", width=150)
else:
    st.title("Rainbow Form")
    
st.write(f"Logged in as: **{st.session_state.user_email}** | Free Tries: **{st.session_state.credits}/3**")

with st.container():
    uploaded_file = st.file_uploader("Upload your drawing...", type=["jpg", "jpeg", "png"])

    if uploaded_file and st.button("🚀 Generate Both Versions (1 Credit)"):
        if st.session_state.credits > 0:
            st.session_state.credits -= 1
            
            with st.spinner("Gemini is sculpting... Saving files securely..."):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3-pro-image-preview')
                    sketch_bytes = uploaded_file.getvalue()

                    # GENERATE UNIQUE ID
                    unique_id = str(uuid.uuid4())[:8]
                    timestamp = datetime.datetime.now().strftime("%Y%m%d")
                    safe_email = st.session_state.user_email.replace("@", "_").replace(".", "_")
                    design_ref = f"{safe_email}_{timestamp}_{unique_id}"
                    st.session_state.current_design_id = design_ref

                    # 1. UPLOAD SKETCH
                    upload_to_drive(sketch_bytes, f"{design_ref}_SKETCH.jpg", uploaded_file.type)

                    # PROMPTS
                    prompt_color = """
                    Turn this drawing into real chunky 3D-printed vinyl toys, following it with extreme accuracy.
                    STRICT RULES — DO NOT FIX ANYTHING:
                    Preserve every proportion, size, thickness, spacing, crooked line, wobble, distortion, scribble, and mistake exactly as drawn. No cleaning, smoothing, correcting, or symmetrizing. Keep all parts the same relative size.
                    COLOR RULE: Use the exact colors from the drawing, but apply them as smooth, even, solid vinyl colors (no scribble texture). White/uncolored regions become smooth white vinyl. If white areas contain lines/symbols, emboss them exactly.
                    SCRIBBLE LOGIC: If scribbles only indicate color, convert to flat solid color. If scribbles represent shapes (hair, rays, hearts, outlines, marks), extrude them as raised chunky vinyl curves following the same irregular path.
                    VINYL FORM RULE: Use “cookie-cutter inflation”: give every shape thick, solid, puffy vinyl volume with rounded front edges, while keeping the original shape exactly.
                    FACE RULE: Facial features must preserve exact position, size, shape, and color.
                    PRESERVATION: Keep all objects, shapes, rays, marks, hearts, and floating elements. No rotation, flipping, or cropping. Match the exact count of figures.
                    RENDER: Clean white infinity-curve studio with visible ground + wall, softbox lighting from top-left, soft grounded shadows, deep focus, matte or lightly glossy vinyl.
                    PACKAGING: Show a white printed laminated box on the left. Print the full original drawing on the box front exactly (no beautifying). Decorate box sides with simple color accents inspired by the drawing. Include any signature if present; otherwise leave blank. Optionally add small “Rainbow Form” text branding.
                    Final output: realistic studio photo of the toy beside its box.
                    ADDITIONAL INPUT INSTRUCTION: Use the provided second image (Rainbow Form Logo) to apply the branding on the box.
                    """

                    prompt_white = """
                    Turn this drawing into a real chunky 3D-printed vinyl toy, following it with extreme accuracy.
                    STRICT RULES — DO NOT FIX ANYTHING:
                    Preserve every proportion, size, thickness, spacing, crooked line, wobble, distortion, scribble, and mistake exactly as drawn. No cleaning, smoothing, correcting, or symmetrizing. Keep all parts the same relative size.
                    COLOR RULE: Create the toy as fully white, unpainted vinyl. Do not apply any of the colors from the drawing to the toy. All surfaces should be clean, smooth white vinyl. If the drawing contains lines or symbols inside white areas, raise or emboss them in white.
                    SCRIBBLE LOGIC: If scribbles represent shapes, convert them into raised, chunky white vinyl curves. If scribbles represent color fill, convert those regions into smooth white vinyl surfaces.
                    VINYL FORM RULE: Use “cookie-cutter inflation”: give every shape thick, solid, puffy vinyl volume with rounded front edges.
                    FACE RULE: Convert facial features into raised or engraved white vinyl shapes.
                    PRESERVATION: Keep all objects, shapes, rays, marks, hearts, and floating elements.
                    RENDER: Clean white infinity-curve studio with visible ground + wall, softbox lighting from top-left, soft grounded shadows, deep focus, matte or lightly glossy white vinyl.
                    PACKAGING: Show a white printed laminated box on the left. Print the full original drawing on the box front exactly. Decorate box sides with simple color accents inspired by the drawing.
                    Final output: a realistic studio photo of the fully white vinyl toy beside its box.
                    ADDITIONAL INPUT INSTRUCTION: Use the provided second image (Rainbow Form Logo) to apply the branding on the box.
                    """

                    # Inputs
                    inputs_color = [prompt_color, {'mime_type': uploaded_file.type, 'data': sketch_bytes}]
                    inputs_white = [prompt_white, {'mime_type': uploaded_file.type, 'data': sketch_bytes}]
                    if logo_data:
                        inputs_color.append(logo_data)
                        inputs_white.append(logo_data)

                    # Generate (Disable Safety)
                    safe = [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                    
                    response_color = model.generate_content(inputs_color, safety_settings=safe)
                    response_white = model.generate_content(inputs_white, safety_settings=safe)

                    # Extract Images
                    img_color = response_color.parts[0].inline_data.data if response_color.parts and response_color.parts[0].inline_data else None
                    img_white = response_white.parts[0].inline_data.data if response_white.parts and response_white.parts[0].inline_data else None
                    
                    # Check for failures
                    if img_color is None or img_white is None:
                        st.error("⚠️ Generation incomplete. Please try again or check billing.")

                    # 2. UPLOAD RESULTS TO DRIVE
                    if img_color:
                        upload_to_drive(img_color, f"{design_ref}_COLOR_PREVIEW.jpg", "image/jpeg")
                    if img_white:
                        upload_to_drive(img_white, f"{design_ref}_WHITE_PREVIEW.jpg", "image/jpeg")

                    st.session_state.generated_images = {
                        "color": img_color,
                        "white": img_white
                    }

                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.error("You are out of credits!")
            # ⬇️ REPLACE WITH YOUR CREDIT PACK ID ⬇️
            credit_url = f"https://rainbowform.com/cart/46397098262776:1?checkout[email]={st.session_state.user_email}"
            st.link_button("⚡ Buy 10 More Credits ($1.99)", credit_url)

# --- 7. RESULTS DISPLAY ---
if st.session_state.generated_images:
    st.divider()
    st.subheader("Choose your version:")
    
    design_id = st.session_state.current_design_id
    
    col_color, col_white = st.columns(2)

    # LEFT: Full Color
    with col_color:
        st.markdown("### 🌈 Full Color Toy")
        if st.session_state.generated_images["color"]:
            st.image(st.session_state.generated_images["color"], use_column_width=True)
            st.markdown("""<div class='price-tag'><span class='original-price'>$69.96</span>$59.99</div>""", unsafe_allow_html=True)
            
            size = st.selectbox("Choose Size", ["Small (5 Inch)", "Medium (6 Inch)", "Large (7 Inch)"], key="s_opt")
            
            color_ids = {
                "Small (5 Inch)": "46397098098936", 
                "Medium (6 Inch)": "46397098131704", 
                "Large (7 Inch)": "46397098164472"
            }
            
            if size in color_ids:
                url = f"https://rainbowform.com/cart/{color_ids[size]}:1?checkout[email]={st.session_state.user_email}&attributes[Design_Ref]={design_id}"
                st.link_button("🛒 Order Color Version", url, type="primary")

    # RIGHT: Color Me
    with col_white:
        st.markdown("### 🎨 'Color Me' (DIY)")
        if st.session_state.generated_images["white"]:
            st.image(st.session_state.generated_images["white"], use_column_width=True)
            st.markdown("""<div class='price-tag'><span class='original-price'>$39.99</span>$29.99</div>""", unsafe_allow_html=True)
            
            paint = st.selectbox("Choose Set", ["Just the Toy", "+ 12 Color Set", "+ 36 Color Set"], key="p_opt")
            
            paint_ids = {
                "Just the Toy": "46397089677560",
                "+ 12 Color Set": "46397089710328",
                "+ 36 Color Set": "46397089743096"
            }
            if paint in paint_ids:
                 url = f"https://rainbowform.com/cart/{paint_ids[paint]}:1?checkout[email]={st.session_state.user_email}&attributes[Design_Ref]={design_id}"
                 st.link_button("🛒 Order DIY Version", url, type="primary")
