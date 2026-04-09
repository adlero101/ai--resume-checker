import streamlit as st
import os
import PyPDF2
from dotenv import load_dotenv
from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage
from azure.core.credentials import AzureKeyCredential

# env file has the token
load_dotenv()
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
ENDPOINT = "https://models.inference.ai.azure.com"
MODEL_NAME = "gpt-4o-mini"
# UI theme
if 'theme' not in st.session_state:
    st.session_state.theme = 'light'

def toggle_theme():
    st.session_state.theme = 'dark' if st.session_state.theme == 'light' else 'light'


dark_css = """
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stHeader"] { background-color: #031341; }
    .stTextArea textarea { background-color: #262730; color: black; border: 1px solid #4B4B4B; }
    .stMarkdown h2, .stMarkdown h1 { color: #00D4FF; }
    div[data-testid="stStatusWidget"] { background-color: #262730; }
</style>
"""
light_css = """
<style>
    /* Main App Background */
    .stApp { background-color: #FFFFFF; color: #31333F; }

    /* 1. Fix the Label (The "invisible" blue text) */
    .stFileUploader label p, .stTextArea label p { 
        color: #000000 !important; 
        font-weight: 500;
    }

    /* 2. Fix the File Uploader Box background and border */
    [data-testid="stFileUploader"] section {
        background-color: #F8F9FB !important; /* Light gray background */
        border: 1px dashed #D1D1D1 !important; /* Soft dashed border */
        color: #31333F !important;
    }

    /* 
    [data-testid="stFileUploader"] section div div {
        color: #31333F !important;
    }

    /* 
    .stTextArea textarea { 
        background-color: #FFFFFF !important; 
        color: #000000 !important; 
        border: 1px solid #D1D1D1 !important; 
    }
    
    .stTextArea textarea::placeholder {
        color: #888888 !important;
    }

    /* Headers */
    .stMarkdown h2, .stMarkdown h1 { color: #000000; }
</style>
"""


def extract_text_from_pdf(uploaded_file):
    """Extract text from a PDF file."""
    try:
        reader = PyPDF2.PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            content = page.extract_text()
            if content:
                text += content
        return text.strip()
    except Exception as e:
        return f"Error: {str(e)}"

def get_ai_analysis(resume_text, job_description):
    """Sends prompt to GitHub Models via Azure AI Inference SDK."""
    if not GITHUB_TOKEN:
        return "🚨ERROR: GITHUB_TOKEN not found in .env. Please check your environment variables."
    
    try:
        # Initializing client inside the function to ensure fresh connection per request
        client = ChatCompletionsClient(
            endpoint=ENDPOINT, 
            credential=AzureKeyCredential(GITHUB_TOKEN)
        )
        
        response = client.complete(
            messages=[
                SystemMessage(content="You are a senior technical recruiter specializing in AI and Computer Science roles. Provide a detailed, critical, yet constructive evaluation."),
                UserMessage(content=f"""
                    Analyze the following Resume against the Job Description (JD).
                    
                    ### JOB DESCRIPTION:
                    {job_description}
                    
                    ### RESUME CONTENT:
                    {resume_text}
                    
                    ### OUTPUT FORMAT (Markdown):
                    1. **Match Score**: [Score]/100
                    2. **Executive Summary**: 2 sentences on overall fit.
                    3. **Key Strengths**: Top 3 matching skills.
                    4. **Critical Gaps**: Missing keywords or requirements.
                    5. **Actionable Advice**: How to improve this specific resume for this role.
                    6. **Wild career ideas**: Suggest the user of other related or unrelated careers.
                """),
            ],
            model=MODEL_NAME,
            temperature=0.1 # Low temperature for consistent, professional analysis
        )
        return response.choices[0].message.content
    except Exception as e:
        return f"API Error: {str(e)}"

# Main UI layout
st.set_page_config(page_title="AI-powered Resume Checker", layout="wide")

# Apply Theme CSS 
st.markdown(
    dark_css if st.session_state.theme == 'dark' else light_css, 
    unsafe_allow_html=True
)

# Sidebar for light and dark
with st.sidebar:
    st.title("App Settings")
    st.button("Switch Theme", on_click=toggle_theme, use_container_width=True)
    st.divider()
    st.info(f"**Engine:** {MODEL_NAME}")
    st.caption("AI can make mistakes. Please double-check before this ruin your life")
    if not GITHUB_TOKEN:
        st.error("Missing API Token!")

# Main UI
st.title("AI-powered Resume Checker")
st.markdown("Everyone has the right to be employed")

# Input Section
col1, col2 = st.columns([1, 1], gap="large")

with col1:
    st.subheader("Job Description")
    jd_input = st.text_area(
        "Paste the requirements here...", 
        height=300, 
        placeholder="Descriptions of your dream job"
    )

with col2:
    st.subheader("Candidate Resume")
    uploaded_file = st.file_uploader("Upload Resume (PDF format)", type="pdf")
    if uploaded_file:
        st.success(f"File '{uploaded_file.name}' ready for analysis.")

st.divider()


if st.button("Full AI Analysis", use_container_width=True, type="primary"):
    if uploaded_file and jd_input.strip():
        # st.status for loading effect
        with st.status("Analyzing your Resume...", expanded=True) as status:
            status.write("Reading PDF document...")
            resume_content = extract_text_from_pdf(uploaded_file)
            
            
            if len(resume_content) < 50:
                status.update(label="Analysis Failed", state="error", expanded=True)
                st.error("The PDF content is too short or unreadable. Please ensure it's in PDF format (not a scanned image).")
            else:
                status.write("Consulting AI Recruitment Expert...")
                analysis_result = get_ai_analysis(resume_content, jd_input)
                
                status.update(label="Analysis Complete!", state="complete", expanded=False)
                
              
                st.subheader("Insights")
                st.markdown(analysis_result)
    else:
        st.warning("Please provide both a Job Description and a Resume file to begin.")