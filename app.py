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
                prompt = f"Summarize the following article in a {summary_type.lower()} format:\n\n{content}"

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
                except Exception as e:
                    st.error(f"OpenAI Error: {e}")
