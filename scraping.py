import json
import requests
from bs4 import BeautifulSoup
import re
import os
import anthropic
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

NUM_PATENTS = 2  # number of results to return
load_dotenv()


def grab_patents(keyphrase):
    options = webdriver.ChromeOptions()
    options.add_argument('--headless')
    driver = webdriver.Chrome()
    url = f"https://patents.google.com/?q=({keyphrase})"
    driver.get(url)
    wait = WebDriverWait(driver, 15)
    wait.until(EC.presence_of_element_located((By.ID, "htmlContent")))
    soup = BeautifulSoup(driver.page_source, "html.parser")
    patents = soup.find_all('article', {'class': 'search-result-item'})

    data = []
    patent_pattern = re.compile('US[0-9]+[A,B][0-2]')
    for i in range(len(patents)):
        if i > NUM_PATENTS:
            break
        if re.search(patent_pattern, patents[i].text) is not None:
            us_patent_number = re.findall(patent_pattern, patents[i].text)[0].strip()
            url = f"https://patents.google.com/patent/{us_patent_number}/en?"
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")
            abstract = soup.find('div', {'class': 'abstract'}).text.strip()
            claims = soup.find('section', {'itemprop': 'claims'}).find_all('div', {'id': re.compile('CLM-[0-9]+')})
            claims = [c.text for c in claims]
            full_description = soup.find('section', {'itemprop': 'description'}).text
            data.append({
                'US Patent Number': us_patent_number,
                'abstract': abstract,
                'description': full_description,
                'claims': claims,
            })

    client = anthropic.Anthropic(
        api_key=os.environ.get("ANTHROPIC_API_KEY")
    )
    message = client.messages.create(
        model="claude-3-haiku-20240307",
        max_tokens=2000,
        system="You are a helpful assistant to a patent attorney that is extremely incisive at delineating the "
               "different components of a patented invention and only outputs answers in json.",
        temperature=0,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": """**Business Pitch: Introducing the Next Generation Smartphone with Revolutionary Moving Camera Lenses**
    
    Dear Potential Investors,
    
    We are thrilled to present our innovative smartphone project aimed at revolutionizing the mobile photography experience – the smartphone with moving camera lenses. In a market inundated with stagnant designs and incremental improvements, our device stands out as a game-changer, offering unparalleled flexibility and creativity to users.
    
    **Overview:**""",
                    }
                ]
            }
        ]
    )
    res = message.content[0].text
    features = json.loads(res.split('<answer>')[-1].split('</answer>')[0].strip())
    print(features)
