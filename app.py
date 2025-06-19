import streamlit as st
import openai
from newspaper import Article
import os


st.set_page_config(page_title="Website Summarizer", layout="centered")
openai.api_key = st.secrets.get("OPENAI_API_KEY", os.getenv("OPENAI_API_KEY"))

st.title("🌐 Website Summarizer")
st.markdown("Paste a news article or blog URL, and get a summary.")

# User Input
url = st.text_input("🔗 Enter the URL of the article:")
summary_type = st.radio(" Summary Type", ["Short", "Detailed"])

if st.button("Summarize"):
    if not url:
        st.warning("Please enter a URL.")
    else:
        with st.spinner("Fetching and summarizing the content..."):
            try:
               
                article = Article(url)
                article.download()
                article.parse()
                content = article.text

                if len(content) < 100:
                    st.error("Failed to extract article content. Try another URL.")
                else:
                  
                    prompt = f"Summarize the following article in a {summary_type.lower()} format:\n\n{content}"

                    
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
                st.error(f"Error: {e}")
