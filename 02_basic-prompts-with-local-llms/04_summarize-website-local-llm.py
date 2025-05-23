import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from openai import OpenAI

load_dotenv()

OLLAMA_API = "http://localhost:11434/v1"

# use any modal
MODEL = "llama3.2:1b"
#MODEL = "qwen2.5:0.5b"

ollama_via_openai = OpenAI(base_url=OLLAMA_API, api_key="ollama")


headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}

class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        soup = BeautifulSoup(response.content, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        for irrelevant in soup.body(["script","style","img","input"]):
            irrelevant.decompose()
        self.text = soup.body.get_text(separator="\n", strip=True)

#web = Website("https://edwarddonner.com")

system_prompt = "You are an assistant that analyzes the contents of a website \
and provides a short summary, ignoring text that might be navigation related. \
Respond in markdown."


def user_prompt_for(website_content):
    user_prompt = f"You are looking at a website titled {website_content.title}"
    user_prompt += "\nThe content of this website is as follows; \
    please provide a short summary of this website in markdown. \
    If it includes news or announcements, then summarize these too. \n\n"
    user_prompt += website_content.text
    return user_prompt

#print(user_prompt_for(web))

def messages_for(website_content):
    return [
        { "role": "system", "content": system_prompt},
        { "role": "user", "content": user_prompt_for(website_content)}
    ]

#messages_for(web)

def summarize(url):
    website = Website(url)
    response = ollama_via_openai.chat.completions.create(
        model=MODEL,
        messages= messages_for(website)
    )
    return response.choices[0].message.content

def display_summary(url):
    summary = summarize(url)
    print(summary)

display_summary("https://edwarddonner.com")