import os
import requests
import json
from typing import List
from dotenv import load_dotenv
from bs4 import BeautifulSoup
from IPython.display import Markdown, display, update_display
from openai import OpenAI

# Load environment variables
load_dotenv()


def openAIGPT4oMiniModal():
    api_key = os.getenv('OPENAI_API_KEY')

    if api_key and api_key.startswith('sk-proj-') and len(api_key)>10:
        print("API key looks good so far")
    else:
        print("There might be a problem with your API key? Please visit the troubleshooting notebook!")
    
    MODEL = 'gpt-4o-mini'
    openai = OpenAI()
    return MODEL,openai

def ollamaAPIModal():
    OLLAMA_API = "http://localhost:11434/v1"

    # use any modal
    MODEL = "llama3.2:1b"
    #MODEL = "qwen2.5:0.5b"

    openai = OpenAI(base_url=OLLAMA_API, api_key="ollama")
    return MODEL,openai


#MODEL, openai = ollamaAPIModal()
MODEL, openai = openAIGPT4oMiniModal()

headers = {
 "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36"
}



class Website:
    def __init__(self, url):
        self.url = url
        response = requests.get(url, headers=headers)
        self.body = response.content
        soup = BeautifulSoup(self.body, 'html.parser')
        self.title = soup.title.string if soup.title else "No title found"
        if soup.body:
            for irrelevant in soup.body(["script", "style", "img", "input"]):
                irrelevant.decompose()
            self.text = soup.body.get_text(separator="\n", strip=True)
        else:
            self.text = ""
        links = [link.get('href') for link in soup.find_all('a')]
        self.links = [link for link in links if link]

    def get_contents(self):
        return f"Webpage Title:\n{self.title}\nWebpage Contents:\n{self.text}\n\n"
    

def get_links_prompt_system():
    link_system_prompt = "You are provided with a list of links found on a webpage. \
You are able to decide which of the links would be most relevant to include in a brochure about the company, \
such as links to an About page, or a Company page, or Careers/Jobs pages.\n"
    link_system_prompt += "You should respond in JSON as in this example:"
    link_system_prompt += """
{
    "links": [
        {"type": "about page", "url": "https://full.url/goes/here/about"},
        {"type": "careers page": "url": "https://another.full.url/careers"}
    ]
}
"""
    return link_system_prompt


def get_links_user_prompt(website):
    user_prompt = f"Here is the list of links on the website of {website.url} - "
    user_prompt += "please decide which of these are relevant web links for a brochure about the company, respond with the full https URL in JSON format. \
Do not include Terms of Service, Privacy, email links.\n"
    user_prompt += "Links (some might be relative links):\n"
    user_prompt += "\n".join(website.links)
    return user_prompt


def get_links(url):
    website = Website(url)
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": get_links_prompt_system()},
            {"role": "user", "content": get_links_user_prompt(website)}
        ],
        response_format={"type": "json_object"}
    )
    result = response.choices[0].message.content
    return json.loads(result)


def get_all_details(url):
    result = "Landing Page:\n"
    result += Website(url).get_contents()
    links = get_links(url)
    print("Found links:", links)
    for link in links['links']:
        result += f"\n\n{link['type']}\n"
        result += Website(link['url']).get_contents()
    print("Result of links:", result)
    return result


def get_brochure_system_prompt():
    brochure_system_prompt = "You are an assistant that analyzes the contents of several relevant pages from a company website \
and creates a short brochure about the company for prospective customers, investors and recruits. Respond in markdown.\
Include details of company culture, customers and careers/jobs if you have the information."
    return brochure_system_prompt

def get_brochure_user_prompt(company_name, url):
    user_prompt = f"You are looking at a company called: {company_name}\n"
    user_prompt += f"Here are the contents of its landing page and other relevant pages; use this information to build a short brochure of the company in markdown.\n"
    user_prompt += get_all_details(url)
    user_prompt += user_prompt[:5_000]
    return user_prompt

def create_brochure(company_name, url):
    response = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": get_brochure_system_prompt()},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ]
    )
    result = response.choices[0].message.content
    #display(Markdown(result))
    print(result)

def stream_brochure(company_name, url):
    stream = openai.chat.completions.create(
        model=MODEL,
        messages=[
            {"role": "system", "content": get_brochure_system_prompt()},
            {"role": "user", "content": get_brochure_user_prompt(company_name, url)}
        ],
        stream=True
    )
    
    response = ""
    display_handle = display(Markdown(response), display_id=True)
    for chunk in stream:
        response += chunk.choices[0].delta.content or ''
        response = response.replace("```","").replace("markdown", "")
        #update_display(Markdown(response), display_id=display_handle.display_id)
        print(response)

#create_brochure("HuggingFace", "https://huggingface.co")
stream_brochure("HuggingFace", "https://huggingface.co")
