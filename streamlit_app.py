import streamlit as st
import PyPDF2
import nltk
import random
import io
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet

# Download NLTK data
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')

# Security: Validate and sanitize PDF
def is_valid_pdf(pdf_file):
    if pdf_file.size > 10_000_000:  # Limit to 10MB
        return False, "File size exceeds 10MB limit."
    if not pdf_file.name.endswith('.pdf'):
        return False, "Only PDF files are allowed."
    return True, ""

# Extract text from PDF
def extract_text_from_pdf(pdf_file):
    try:
        pdf_reader = PyPDF2.PdfReader(pdf_file)
        text = "".join(page.extract_text() or "" for page in pdf_reader.pages)
        return text
    except Exception as e:
        st.error(f"Error reading PDF: {e}")
        return None

# Generate MCQs with difficulty
def generate_mcqs(text, num_questions=5, difficulty="Medium"):
    sentences = nltk.sent_tokenize(text)
    mcqs = []
    
    for sentence in random.sample(sentences, min(num_questions, len(sentences))):
        doc = nltk.pos_tag(nltk.word_tokenize(sentence))
        nouns = [word for word, pos in doc if pos.startswith('NN')]
        verbs = [word for word, pos in doc if pos.startswith('VB')]
        
        if nouns and verbs:
            correct_answer = random.choice(nouns)
            distractors = generate_distractors(nouns, correct_answer, difficulty)
            
            question = sentence.replace(correct_answer, "______")
                
            mcqs.append({
                "question": question,
                "options": [correct_answer] + distractors,
                "correct": correct_answer,
                "difficulty": difficulty
            })
    return mcqs

def generate_distractors(nouns, correct_answer, difficulty):
    if difficulty == "Easy":
        return random.sample([w for w in nouns if w != correct_answer] + ["None", "All", "Not mentioned"], 3)
    elif difficulty == "Hard":
        return random.sample([w + "ism" for w in nouns if w != correct_answer] + 
                           [correct_answer[:-1] + "x", "Not applicable", "Data insufficient"], 3)
    else:
        return random.sample([w for w in nouns if w != correct_answer] + 
                           ["None of the above", "All of the above", "Not mentioned"], 3)

# Export MCQs to PDF
def export_to_pdf(mcqs):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    for i, mcq in enumerate(mcqs, 1):
        story.append(Paragraph(f"<b>Question {i} ({mcq['difficulty']})</b>: {mcq['question']}", styles['Normal']))
        for j, option in enumerate(mcq['options'], 1):
            story.append(Paragraph(f"{j}. {option}", styles['Normal']))
        story.append(Paragraph(f"<b>Answer</b>: {mcq['correct']}", styles['Normal']))
        story.append(Spacer(1, 12))
    
    doc.build(story)
    buffer.seek(0)
    return buffer

# Mock Authentication
def check_auth():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        password = st.text_input("Enter Password", type="password")
        if password == "test123":  # Replace with your auth logic
            st.session_state.authenticated = True
        else:
            st.error("Please authenticate to continue")
            return False
    return True

# Main app
def main():
    st.set_page_config(page_title="MCQ Generator Pro", layout="wide", initial_sidebar_state="expanded")
    
    # Professional UI
    st.markdown("""
        <style>
        .main {background-color: #f8f9fa;}
        .stButton>button {background-color: #007bff; color: white; border-radius: 5px;}
        .stContainer {border: 1px solid #dee2e6; border-radius: 5px; padding: 20px; margin-bottom: 20px;}
        </style>
    """, unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.title("MCQ Generator Pro")
        st.write("Generate professional MCQs from your PDFs")
        
    # Authentication
    if not check_auth():
        return
    
    # Main content
    st.title("MCQ Generator Professional")
    st.write("Create customized MCQs with advanced options")
    
    uploaded_file = st.file_uploader("Upload PDF Document", type="pdf", help="Max size: 10MB")
    
    if uploaded_file:
        is_valid, error_msg = is_valid_pdf(uploaded_file)
        if not is_valid:
            st.error(error_msg)
            return
        
        with st.spinner("Processing PDF..."):
            text = extract_text_from_pdf(uploaded_file)
        
        if text:
            with st.container():
                st.subheader("MCQ Settings")
                num_questions = st.slider("Number of Questions", 1, 20, 5)
                difficulty = st.selectbox("Difficulty Level", ["Easy", "Medium", "Hard"])
                
                if st.button("Generate MCQs", key="generate"):
                    with st.spinner("Generating MCQs..."):
                        mcqs = generate_mcqs(text, num_questions, difficulty)
                        
                    if mcqs:
                        st.success("MCQs Generated Successfully!")
                        for i, mcq in enumerate(mcqs, 1):
                            with st.container():
                                st.subheader(f"Question {i} ({mcq['difficulty']})")
                                st.write(mcq['question'])
                                for j, option in enumerate(mcq['options'], 1):
                                    st.write(f"{j}. {option}")
                                with st.expander("Show Answer"):
                                    st.success(f"Correct Answer: {mcq['correct']}")
                        
                        # Export to PDF button
                        pdf_buffer = export_to_pdf(mcqs)
                        st.download_button(
                            label="Export to PDF",
                            data=pdf_buffer,
                            file_name="mcqs.pdf",
                            mime="application/pdf",
                            key="download_pdf"
                        )

if __name__ == "__main__":
    main()