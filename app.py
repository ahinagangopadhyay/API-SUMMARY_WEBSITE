import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup
import os
from fpdf import FPDF
import base64
from io import BytesIO
import PyPDF2
from langchain.chains import RetrievalQA
from langchain.chat_models import ChatOpenAI
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import FAISS
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.docstore.document import Document

# Page config
st.set_page_config(page_title="Smart Summarizer & Q&A", layout="centered")
st.title("DocuIntel")

# Load API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# --- Functions ---

def extract_text_from_url(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        return content
    except Exception:
        return None

def extract_text_from_pdf(pdf_file):
    pdf_reader = PyPDF2.PdfReader(pdf_file)
    text = ""
    for page in pdf_reader.pages:
        text += page.extract_text()
    return text

def create_pdf(text):
    safe_text = text.replace("\ufb01", "fi")
    safe_text = safe_text.encode('latin-1', 'ignore').decode('latin-1')
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in safe_text.split("\n"):
        pdf.multi_cell(0, 10, line)
    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return BytesIO(pdf_bytes)

def download_pdf_button(text):
    pdf_buffer = create_pdf(text)
    b64 = base64.b64encode(pdf_buffer.read()).decode()
    return f'<a href="data:application/pdf;base64,{b64}" download="summary.pdf">📄 Download Summary as PDF</a>'

def generate_summary(text, summary_type):
    prompt = f"Summarize the following text in a {summary_type.lower()} format:\n\n{text}"
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
        max_tokens=800
    )
    return response['choices'][0]['message']['content']

def setup_qa(text):
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    docs = splitter.create_documents([text])
    embeddings = OpenAIEmbeddings()
    vectordb = FAISS.from_documents(docs, embeddings)
    retriever = vectordb.as_retriever(search_type="similarity", search_kwargs={"k": 3})
    qa_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(temperature=0),
        retriever=retriever,
        return_source_documents=True
    )
    return qa_chain

# --- Tabs ---
tab1, tab2 = st.tabs(["📝 Summary", "❓ Q&A"])

# --- Summary Tab ---
with tab1:
    st.header("Summarize Content")
    summary_mode = st.radio("Select Input Type", ["🌐 URL", "📄 PDF"])
    summary_type = st.selectbox("Summary Style", ["Short", "Detailed", "Bullet Points"])

    if summary_mode == "🌐 URL":
        url = st.text_input("Enter URL:")
        if st.button("Summarize URL"):
            with st.spinner("Extracting and summarizing..."):
                text = extract_text_from_url(url)
                if not text:
                    st.error("Failed to extract content.")
                else:
                    summary = generate_summary(text, summary_type)
                    st.subheader("✅ Summary")
                    st.write(summary)
                    st.markdown(download_pdf_button(summary), unsafe_allow_html=True)

    elif summary_mode == "📄 PDF":
        uploaded_file = st.file_uploader("Upload a PDF", type="pdf", key="pdf_sum")
        if uploaded_file and st.button("Summarize PDF"):
            with st.spinner("Extracting and summarizing..."):
                text = extract_text_from_pdf(uploaded_file)
                if not text:
                    st.error("Could not extract content.")
                else:
                    summary = generate_summary(text, summary_type)
                    st.subheader("✅ Summary")
                    st.write(summary)
                    st.markdown(download_pdf_button(summary), unsafe_allow_html=True)

# --- Q&A Tab ---
with tab2:
    st.header("Ask Questions from Document or URL")
    qa_mode = st.radio("Select Input Type", ["🌐 URL", "📄 PDF"], key="qa_mode")

    if "qa_text" not in st.session_state:
        st.session_state.qa_text = ""

    if qa_mode == "🌐 URL":
        url = st.text_input("Enter URL for Q&A:")
        if st.button("Load URL Content"):
            with st.spinner("Extracting content..."):
                text = extract_text_from_url(url)
                if not text:
                    st.error("Failed to extract content.")
                else:
                    st.session_state.qa_text = text

    elif qa_mode == "📄 PDF":
        uploaded_file = st.file_uploader("Upload PDF for Q&A", type="pdf", key="qa_pdf")
        if uploaded_file and st.button("Load PDF Content"):
            with st.spinner("Extracting content..."):
                text = extract_text_from_pdf(uploaded_file)
                if not text:
                    st.error("Could not extract content.")
                else:
                    st.session_state.qa_text = text

    # Q&A section only shown if text is successfully loaded
    if st.session_state.qa_text:
        st.success("✅ Content loaded! Ask your question below:")
        user_query = st.text_input("Your question:", key="qa_input")
        if user_query:
            with st.spinner("Generating answer..."):
                qa_chain = setup_qa(st.session_state.qa_text)
                result = qa_chain({"query": user_query})
                st.markdown("**💬 Answer:**")
                st.write(result["result"])

                with st.expander("📄 Retrieved Context"):
                    for doc in result["source_documents"]:
                        st.markdown(doc.page_content)
