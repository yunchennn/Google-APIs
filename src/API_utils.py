import requests
from datetime import datetime, timedelta
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup
import time
from typing import Optional, List, Dict, Any
from collections import defaultdict
import re

def search_google_patents(terms: list, start_date:datetime, end_date:datetime, batch=0):
    """
    return structure
    {
        "position": "",
        "rank": "",
        "patent_id": "patent/US20230105838A1/en",
        "title": "Method of Treating COVID-19",
        "snippet": "1 . A method of treating COVID-19 in a patient, the method comprising administering to a patient in need thereof a therapeutically effective amount of a compound selected from the group consisting of: (3S)-3-({N-[(4-methoxy-1H-indol-2-yl)carbonyl]-L-leucyl}amino)-2-oxo-4-[(3S)-2-oxopyrrolidin-3-yl] …",
        "priority_date": "2020-04-05",
        "filing_date": "2021-04-01",
        "publication_date": "2023-04-06",
        "inventor": "Robert Louis Hoffman",
        "assignee": "Pfizer Inc.",
        "publication_number": "US20230105838A1",
        "language": "en",
        "thumbnail": "https://patentimages.storage.googleapis.com/b1/07/e6/d6e413a09bf1f1/US20230105838A1-20230406-D00001.png",
        "pdf": "https://patentimages.storage.googleapis.com/c0/3a/56/6d01a9d3ef18ee/US20230105838A1.pdf",
        "figures": [ 
            "https://patentimages.storage.googleapis.com/81/d3/eb/d7446ff2374ecd/US20230105838A1-20230406-D00001.png",
            "https://patentimages.storage.googleapis.com/ed/ac/b0/b77d82bfbd2fe2/US20230105838A1-20230406-D00002.png"
        ],
        "country_status": {
            "WO": "ACTIVE",
            "US": "ACTIVE"
        }
    }
    """
    start_date_str = start_date.strftime('%Y%m%d')
    end_date_str = end_date.strftime('%Y%m%d')
    all_results = list()
    idx = 0
    for term in terms:
        for num in range(batch):
            base_url = f"https://patents.google.com/"
            term_name = term.replace(" ", "+").lower()
            url = f'{base_url}?q=({term_name})&before=priority:{end_date_str}&after=priority:{start_date_str}&oq={term_name}&page={num}'
            # print(url)

            options = Options()
            options.add_argument("--headless")
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            time.sleep(5)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            results = soup.find_all("search-result-item")

            for item in results:
                title = item.find("span", id='htmlContent')
                title_txt = title.get_text(strip=True) if title else ""

                patent_id_tag = item.find('state-modifier', {'class': 'result-title style-scope search-result-item'})
                patent_id_txt = patent_id_tag['data-result'] if patent_id_tag and patent_id_tag.has_attr('data-result') else ""

                info = item.find("div", class_='flex style-scope search-result-item')

                date_txt = ""
                priority_date_txt = filing_date_txt = publication_date_txt = ""
                date = info.find('h4', class_='dates style-scope search-result-item') if info else None
                if date:
                    date_txt = date.get_text(strip=True)
                    parts = [part.strip() for part in date_txt.split('•')]
                    for part in parts:
                        if 'Priority' in part:
                            priority_date_txt = part.split(' ')[-1]
                        elif 'Filed' in part:
                            filing_date_txt = part.split(' ')[-1]
                        elif 'Published' in part:
                            publication_date_txt = part.split(' ')[-1]

                activateDict = defaultdict(str)
                if info:
                    activate = info.find_all('span', class_='active style-scope search-result-item')
                    for act in activate:
                        activateDict[act.get_text(strip=True)] = "ACTIVATE"
                    unknown = info.find_all('span', class_='unknown style-scope search-result-item')
                    for act in unknown:
                        activateDict[act.get_text(strip=True)] = "UNKNOWN"

                pdfLink_txt = ""
                if info:
                    pdfLink = info.find('a', class_='pdfLink')
                    if pdfLink and pdfLink.has_attr('href'):
                        pdfLink_txt = pdfLink['href']

                real_id_txt = ""
                if info:
                    patent_real_id = info.find('span', {'data-proto': 'OPEN_PATENT_PDF'})
                    if patent_real_id:
                        real_id_txt = patent_real_id.get_text(strip=True)

                inventor_txt, assignee_txt, snippet_txt = "", "", ""
                if info:
                    name_info = info.find_all('raw-html')
                    raw_data = []
                    for name in name_info:
                        name2 = name.find('span', id='htmlContent')
                        if name2:
                            raw_data.append(name2.get_text(strip=True))
                    if len(raw_data) >= 3:
                        inventor_txt, assignee_txt, snippet_txt = raw_data[0], raw_data[1], raw_data[2]

                figures = []
                if info:
                    imgs = info.find_all('img', class_='thumbnail style-scope search-result-item')
                    for img in imgs:
                        if img.has_attr('src'):
                            figures.append(img['src'])

                sample = {
                    "position": num,
                    "rank": idx,
                    "patent_id": patent_id_txt,
                    "title": title_txt,
                    "snippet": snippet_txt,
                    "priority_date": priority_date_txt,
                    "filing_date": filing_date_txt,
                    "publication_date": publication_date_txt,
                    "inventor": inventor_txt,
                    "assignee": assignee_txt,
                    "publication_number": real_id_txt,
                    "pdf": pdfLink_txt,
                    "figures": figures,
                    "country_status": activateDict
                }

                all_results.append(sample)
                idx+=1

            driver.quit()

    return all_results

def search_google_scholar(terms:list, start_year:datetime, end_year:datetime, patent:bool=True, vis:bool=True, sort_w_related:bool=True, batch=0):
    start_year_str = start_year.strftime('%Y')
    end_year_str = end_year.strftime('%Y')
    vis_int = 1 if vis == True else 0
    patent_str = "7,33" if patent == True else "0,33"
    rel_int = 0 if sort_w_related == True else 1
  
    all_results = list()
    idx = 0
    for term in terms:
        for num in range(batch):
            base_url = f"https://scholar.google.com/scholar"
            term_name = term.replace(" ", "+").lower()
            url = f'{base_url}?as_vis={vis_int}&q="{term_name}"&as_sdt={patent_str}&as_ylo={start_year_str}&as_yhi={end_year_str}&scisbd={rel_int}&start={num*10}'
            # print(url)

            options = Options()
            options.add_argument("--headless")
            service = Service()
            driver = webdriver.Chrome(service=service, options=options)
            driver.get(url)

            time.sleep(5)
            soup = BeautifulSoup(driver.page_source, "html.parser")
            results = soup.find_all("div", class_="gs_r gs_or gs_scl")
            for item in results:
                title = item.find("h3", class_="gs_rt").get_text(strip=True)
                a_tag = soup.find('h3', class_='gs_rt').find('a')
                href = a_tag['href']
                pdf_link = soup.find('div', class_='gs_or_ggsm').find('a')['href']
                div = soup.find('div', class_='gs_rs')

                for b in div.find_all('b'):
                    b.string = ''

                for br in div.find_all('br'):
                    br.replace_with(' ')  

                snippet = div.get_text(strip=True)

                ref_div = item.find("div", class_="gs_fl gs_flb")
                citation_count = None

                if ref_div:
                    a_tags = ref_div.find_all("a")
                    if len(a_tags) >= 3:
                        third_a = a_tags[2]
                        match = re.search(r'\d+', third_a.text)
                        if match:
                            citation_count = int(match.group())

                detail = item.find("div", class_="gs_a")
                authors = [a.text for a in detail.find_all('a')]

                text = detail.get_text()
                rest = [r.strip() for r in text.split(',') if r.strip()]  

                if len(rest) >= 2:
                    publisher = rest[-1]
                    year = publisher.split(' - ')[0]
                    pub = publisher.split(' - ')[-1]

                    journal = rest[-2].split('-')[-1].strip() 
                else:
                    publisher = journal = "N/A"

                sample = {
                    "position": num,
                    "rank": idx,
                    "title":title,
                    "cited": citation_count,
                    "url":href,
                    "pdfLink":pdf_link,
                    "snippet":snippet,
                    "authors":authors,
                    "journal":journal,
                    "publisher":pub,
                    "year": year
                }
                all_results.append(sample)


            driver.quit()

    return all_results


if __name__ == "__main__":
    # test case
    terms = ["coronavirus disease of 2019", "covid-19"]
    years = 10
    end_date = datetime.now()
    start_date = end_date - timedelta(days=365 * years)
    batch = 5 # get 5 pages
    # res = search_google_patents(terms, start_date, end_date, batch)
    # print(res)
    # print(len(res))

    res = search_google_scholar(terms, start_date, end_date, False, True, True, 2)
    









     

    
# 

