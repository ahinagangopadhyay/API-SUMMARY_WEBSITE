import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup
import os
from textblob import TextBlob
import spacy
from fpdf import FPDF
import base64
from io import BytesIO

# Load SpaCy
nlp = spacy.load("en_core_web_sm")

# Streamlit config
st.set_page_config(page_title="Website Summarizer", layout="centered")
openai.api_key = os.getenv("OPENAI_API_KEY")

st.title("🌐 Website Summarizer")
st.markdown("Paste a news/blog URL and get a summary with sentiment and keywords.")

# User Input
url = st.text_input("🔗 Enter the URL of the article:")
summary_type = st.radio("📝 Summary Type", ["Short", "Detailed", "Bullet Points"])

def extract_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Clean HTML
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        return content.strip()
    except Exception:
        return None

def create_pdf(text):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_font("Arial", size=12)
    for line in text.split("\n"):
        pdf.multi_cell(0, 10, line)

    # Get PDF as bytes
    pdf_bytes = pdf.output(dest='S').encode('latin-1')  # 'S' returns as string
    pdf_buffer = BytesIO(pdf_bytes)
    return pdf_buffer


def extract_article_text(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        # Remove scripts and styles
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()

        paragraphs = soup.find_all("p")
        content = "\n".join([p.get_text(strip=True) for p in paragraphs])
        return content.strip()
    except Exception as e:
        return None

if st.button("Summarize"):
    if not url:
        st.warning("Please enter a URL.")
    else:
        with st.spinner("Fetching and summarizing the content..."):
            content = extract_article_text(url)

            if not content or len(content) < 100:
                st.error("Failed to extract article content. Try another URL.")
            else:
                # Generate prompt
                prompt_style = {
                    "Short": "Give a short summary:",
                    "Detailed": "Give a detailed summary:",
                    "Bullet Points": "Summarize the following article as bullet points:"
                }
                prompt = f"{prompt_style[summary_type]}\n\n{content}"

                try:
                    response = openai.ChatCompletion.create(
                        model="gpt-3.5-turbo",
                        messages=[{"role": "user", "content": prompt}],
                        temperature=0.7,
                        max_tokens=800
                    )
                    summary = response['choices'][0]['message']['content']

                    st.success("✅ Summary:")
                    st.write(summary)

                    # Keywords
                    doc = nlp(content)
                    keywords = list(set(ent.text for ent in doc.ents if len(ent.text.split()) < 5))
                    if keywords:
                        st.markdown("**🔑 Keywords/Entities:** " + ", ".join(keywords))

                    # Sentiment
                    sentiment = TextBlob(content).sentiment
                    st.markdown(f"**🧠 Sentiment:** Polarity = `{sentiment.polarity:.2f}`, Subjectivity = `{sentiment.subjectivity:.2f}`")

                    # PDF Download (Fixed)
                    pdf_buffer = create_pdf(summary)
                    b64 = base64.b64encode(pdf_buffer.read()).decode()
                    href = f'<a href="data:application/pdf;base64,{b64}" download="summary.pdf">📄 Download Summary as PDF</a>'
                    st.markdown(href, unsafe_allow_html=True)

                except Exception as e:
                    st.error(f"OpenAI API Error: {e}")
