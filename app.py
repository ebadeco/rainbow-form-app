import streamlit as st
import google.generativeai as genai
from PIL import Image
import io
import os
import re

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Rainbow Form Portal", page_icon="🎨", layout="wide")

st.markdown("""
    <style>
    /* 1. HIDE STREAMLIT BRANDING */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* 2. BACKGROUND & FONTS */
    .stApp {
        background-color: #ffffff; /* Matches Shopify White Background */
        font-family: 'Helvetica', 'Arial', sans-serif;
    }

    /* 3. PRODUCT CARDS (Shadows & Borders) */
    div[data-testid="column"] {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 20px;
        box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        border: 1px solid #f0f0f0;
        transition: transform 0.2s;
    }
    div[data-testid="column"]:hover {
        transform: translateY(-5px);
    }

    /* 4. BUTTONS (The Rainbow Form Look) */
    div.stButton > button {
        width: 100%;
        border-radius: 12px;
        font-weight: 700;
        height: 55px;
        text-transform: uppercase;
        letter-spacing: 1px;
        border: none;
        background: linear-gradient(90deg, #FF9A9E 0%, #FECFEF 99%, #FECFEF 100%);
        color: white !important;
        box-shadow: 0 4px 15px rgba(255, 100, 150, 0.4);
    }
    div.stButton > button:hover {
        background: linear-gradient(90deg, #ff758c 0%, #ff7eb3 100%);
        box-shadow: 0 6px 20px rgba(255, 100, 150, 0.6);
        color: white !important;
    }

    /* 5. PRICE TAGS */
    .price-tag {
        font-size: 1.4em;
        font-weight: 800;
        color: #2e7d32;
        margin-bottom: 10px;
        font-family: 'Courier New', monospace;
    }
    .original-price {
        text-decoration: line-through;
        color: #999;
        font-size: 0.7em;
        margin-right: 8px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 2. SECURE API KEY ---
try:
    api_key = st.secrets["GOOGLE_API_KEY"]
except:
    st.error("⚠️ Server Error: API Key missing. Please check Streamlit Secrets.")
    st.stop()

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

# --- 5. LOGIN GATEKEEPER ---
if not st.session_state.user_email:
    col1, col2, col3 = st.columns([1,2,1])
    with col2:
        # FIXED: Proper If/Else block to prevent printing code
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
# FIXED: Proper If/Else block to prevent printing code
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
            
            with st.spinner("Gemini is sculpting Color AND White versions... (Wait ~30s)"):
                try:
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel('gemini-3-pro-image-preview')
                    sketch_bytes = uploaded_file.getvalue()

                    # --- PROMPT 1: FULL COLOR ---
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

                    # --- PROMPT 2: WHITE PRIMER ---
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

                    # Generate (With Safety Filter disabled)
                    safe = [
                        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
                        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
                    ]
                    
                    response_color = model.generate_content(inputs_color, safety_settings=safe)
                    response_white = model.generate_content(inputs_white, safety_settings=safe)

                    # Extract Images
                    img_color = None
                    if response_color.parts and response_color.parts[0].inline_data:
                        img_color = response_color.parts[0].inline_data.data

                    img_white = None
                    if response_white.parts and response_white.parts[0].inline_data:
                        img_white = response_white.parts[0].inline_data.data

                    # Error Check
                    if img_color is None or img_white is None:
                        st.error("⚠️ Generation Incomplete. Note: Billing must be active on your Google Cloud Project for this model.")

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
    
    col_color, col_white = st.columns(2)

    # LEFT: Full Color
    with col_color:
        st.markdown("### 🌈 Full Color Toy")
        if st.session_state.generated_images["color"]:
            st.image(st.session_state.generated_images["color"], use_column_width=True)
            
            st.markdown("""
            <div class='price-tag'>
                <span class='original-price'>$69.96</span>$59.99
            </div>
            """, unsafe_allow_html=True)
            
            size = st.selectbox("Choose Size", ["Small (5 Inch)", "Medium (6 Inch)", "Large (7 Inch)"], key="s_opt")
            
            color_ids = {
                "Small (5 Inch)": "46397098098936", 
                "Medium (6 Inch)": "46397098131704", 
                "Large (7 Inch)": "46397098164472"
            }
            if size in color_ids:
                url = f"https://rainbowform.com/cart/{color_ids[size]}:1?checkout[email]={st.session_state.user_email}"
                st.link_button("🛒 Order Color Version", url, type="primary")
        else:
            st.warning("Preview unavailable.")

    # RIGHT: Color Me
    with col_white:
        st.markdown("### 🎨 'Color Me' (DIY)")
        if st.session_state.generated_images["white"]:
            st.image(st.session_state.generated_images["white"], use_column_width=True)
            
            st.markdown("""
            <div class='price-tag'>
                <span class='original-price'>$39.99</span>$29.99
            </div>
            """, unsafe_allow_html=True)
            
            paint = st.selectbox("Choose Set", ["Just the Toy", "+ 12 Color Set", "+ 36 Color Set"], key="p_opt")
            
            paint_variant_ids = {
                "Just the Toy": "46397089677560",
                "+ 12 Color Set": "46397089710328",
                "+ 36 Color Set": "46397089743096"
            }
            if paint in paint_variant_ids:
                 url = f"https://rainbowform.com/cart/{paint_variant_ids[paint]}:1?checkout[email]={st.session_state.user_email}"
                 st.link_button("🛒 Order DIY Version", url, type="primary")
        else:
            st.warning("Preview unavailable.")
