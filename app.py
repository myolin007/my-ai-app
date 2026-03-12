import streamlit as st
import os
import tempfile
import time
from google import genai
from google.genai import types

# Constants
SYSTEM_PROMPT = """
You are an elite Burmese Subtitle Translator with expertise in Chinese entertainment media.
Your task is to watch the video, listen to the audio, and generate time-synced subtitles in Burmese (Myanmar) SRT format.

PHASE 1: CONTEXTUAL ANALYSIS (Internal Processing)
Before translating, analyze the video for:
Genre & Tone: 
- Is it a Comedy? (Use slang, funny particles like 'ကွ', 'ဟ', 'နော်').
- Is it a Serious Drama/Business? (Use polite but firm language).

Speaker Relationships: 
- Identify Boss vs. Employee (Boss uses authoritative tone, Employee uses respectful tone).
- Identify Close Friends (Casual tone).

Names vs. Titles: 
- Distinguish between a Name (e.g., "Ah Ji") and a Title (e.g., "Manager").
- Transliterate names phonetically (e.g., "Li Wan Ji" -> "လီဝမ်ကျီး").

PHASE 2: TRANSLATION RULES (Strict Adherence)
Natural Spoken Burmese: Do NOT translate word-for-word. Translate the intent and meaning.
Example: "大半年一张单没开" -> DO NOT translate as "Didn't open a sheet/bill".
CORRECT: "တစ်နှစ်ဝက်ကျော်နေပြီ အော်ဒါတစ်ခုမှ မရသေးဘူး" or "အရောင်းစာရင်း တစ်စောင်မှ မဖွင့်နိုင်သေးဘူး".

Business Terminology: 
- Use English loanwords if they are common in Burmese business context (e.g., "Order", "Project", "Manager", "Meeting").

Idioms & Slang: Capture the emotion. If they are arguing, make the Burmese sound heated.

OUTPUT FORMAT:
Provide ONLY the valid SRT content. No conversational filler.
The output must start immediately with the first SRT block.
"""

VIRAL_TITLE_PROMPT = """
You are a Viral Title Generator for Burmese funny videos. Task: Generate 5 catchy, funny, and clickbait-style Burmese titles based on the provided video content. Constraints:

DO NOT say 'Yes', 'Okay', 'Here are the titles', or 'ဟုတ်ကဲ့'.

DIRECTLY output the list of 5 titles.

Use emojis appropriate for comedy (🤣, 😂, 💀).

If the input is empty, return 'စာသားမရှိပါ'.
"""

AVAILABLE_MODELS = {
    'gemini-3-flash-preview': 'Gemini 3 Flash (Fast)',
    'gemini-3-pro-preview': 'Gemini 3 Pro (High Intel)'
}

st.set_page_config(page_title="Burmese Subtitle Studio", page_icon="🤖", layout="wide")

# Custom CSS for dark theme similar to the original React app
st.markdown("""
<style>
    .stApp {
        background-color: #0d1117;
        color: #e2e8f0;
    }
    .stButton>button {
        background: linear-gradient(to right, #d97706, #b45309);
        color: white;
        border: none;
        border-radius: 0.75rem;
        font-weight: bold;
        padding: 0.75rem 1rem;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        background: linear-gradient(to right, #f59e0b, #d97706);
        transform: translateY(-2px);
    }
    h1, h2, h3 {
        color: #f3f4f6 !important;
    }
</style>
""", unsafe_allow_html=True)

st.title("🤖 Burmese Subtitle Studio")
st.markdown("**Powered by Gemini 3**")
st.markdown("Upload your Chinese entertainment clips. Our AI analyzes tone, relationships, and context to deliver elite-tier, culturally accurate Burmese subtitles.")

api_key = os.environ.get("GEMINI_API_KEY")
if not api_key:
    st.warning("API Key not found in environment variables. Please set GEMINI_API_KEY.")
    api_key = st.text_input("Enter GEMINI_API_KEY manually:", type="password")
    if not api_key:
        st.stop()

client = genai.Client(api_key=api_key)

col1, col2 = st.columns(2)

with col1:
    st.subheader("1. Source Media")
    uploaded_file = st.file_uploader("Upload Video", type=["mp4", "mov", "avi", "mkv", "webm"])
    
    if uploaded_file is not None:
        st.video(uploaded_file)
        
        st.subheader("Translation Config")
        selected_model_id = st.selectbox(
            "Model",
            options=list(AVAILABLE_MODELS.keys()),
            format_func=lambda x: AVAILABLE_MODELS[x]
        )
        
        col_btn1, col_btn2 = st.columns(2)
        
        with col_btn1:
            if st.button("✨ Generate Subtitles", use_container_width=True):
                st.session_state.generating_subtitles = True
                st.session_state.subtitles = None
                
        with col_btn2:
            if st.button("⚡ Viral Titles", use_container_width=True):
                st.session_state.generating_titles = True
                st.session_state.viral_titles = None

def upload_to_gemini(file_obj, mime_type):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        tmp.write(file_obj.getvalue())
        tmp_path = tmp.name
    
    uploaded_file_info = client.files.upload(file=tmp_path, config={'mime_type': mime_type})
    os.unlink(tmp_path)
    
    # Wait for the file to be active
    while getattr(uploaded_file_info.state, "name", uploaded_file_info.state) == "PROCESSING":
        time.sleep(2)
        uploaded_file_info = client.files.get(name=uploaded_file_info.name)
        
    if getattr(uploaded_file_info.state, "name", uploaded_file_info.state) == "FAILED":
        raise Exception("File processing failed on Gemini servers.")
        
    return uploaded_file_info

with col2:
    st.subheader("2. Results")
    
    if uploaded_file is not None:
        if getattr(st.session_state, 'generating_subtitles', False):
            with st.spinner("Generating subtitles..."):
                try:
                    gemini_file = upload_to_gemini(uploaded_file, uploaded_file.type)
                    
                    response = client.models.generate_content(
                        model=selected_model_id,
                        contents=[
                            gemini_file,
                            "Generate Burmese SRT subtitles for this video."
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=SYSTEM_PROMPT,
                            temperature=0.4,
                        )
                    )
                    st.session_state.subtitles = response.text
                except Exception as e:
                    st.error(f"Error generating subtitles: {e}")
                finally:
                    st.session_state.generating_subtitles = False
                    
        if getattr(st.session_state, 'subtitles', None):
            st.text_area("SRT Subtitles", st.session_state.subtitles, height=400)
            st.download_button(
                label="Download SRT",
                data=st.session_state.subtitles,
                file_name="subtitles.srt",
                mime="text/plain"
            )
            
        if getattr(st.session_state, 'generating_titles', False):
            with st.spinner("Generating viral titles..."):
                try:
                    gemini_file = upload_to_gemini(uploaded_file, uploaded_file.type)
                    
                    response = client.models.generate_content(
                        model=selected_model_id,
                        contents=[
                            gemini_file,
                            "Generate 5 viral Burmese titles for this video."
                        ],
                        config=types.GenerateContentConfig(
                            system_instruction=VIRAL_TITLE_PROMPT,
                            temperature=0.9,
                            max_output_tokens=500,
                        )
                    )
                    st.session_state.viral_titles = response.text
                except Exception as e:
                    st.error(f"Error generating titles: {e}")
                finally:
                    st.session_state.generating_titles = False
                    
        if getattr(st.session_state, 'viral_titles', None):
            st.markdown("### Viral Titles")
            st.info(st.session_state.viral_titles)
    else:
        st.info("Upload a video and click generate to see results here.")
