import streamlit as st
import openai
import requests
from bs4 import BeautifulSoup
import os

st.set_page_config(page_title="Website Summarizer", layout="centered")
openai.api_key = os.getenv("OPENAI_API_KEY")
<<<<<<< HEAD

=======
>>>>>>> 94fc974 (Updated app.py with new summarization logic)

st.title("🌐 Website Summarizer")
st.markdown("Paste a news article or blog URL, and get a summary.")

# User Input
url = st.text_input("🔗 Enter the URL of the article:")
summary_type = st.radio(" Summary Type", ["Short", "Detailed"])

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
                    st.success("Here’s the summary:")
                    st.write(summary)
                except Exception as e:
                    st.error(f"OpenAI Error: {e}")
