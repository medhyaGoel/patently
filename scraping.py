import requests
from bs4 import BeautifulSoup
import re
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver import ChromeService

NUM_PATENTS = 2  # number of results to return
load_dotenv()

opts = webdriver.ChromeOptions()
opts.add_argument('--headless')
# driver = webdriver.Chrome()
driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=opts)


def grab_patents(keyphrase):
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
    return data
