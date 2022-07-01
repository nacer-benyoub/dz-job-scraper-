import requests
import json
import pandas as pd
from bs4 import BeautifulSoup as bs

def make_soup(limit=50, page=1):
    """Generate BeautifulSoup object for the local variable 'url'

    Args:
        limit (int, optional): number of results per page. Defaults to 50.
        page (int, optional): number of pages. Defaults to 1.

    Returns:
        bs4.BeautifulSoup: BeautifulSoup object
    """
    start = (page-1) * 50
    url = "https://www.emploitic.com/offres-d-emploi?limit={0}&start={1}".format(limit, start)
    # get the user agent from 'edge://version/' in Microsoft Edge 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44'}
    response = requests.get(url, headers=headers)
    soup = bs(response.text, 'html.parser')
    return soup

def scarpe_jobs(soup):
    """Scrape job details from the BeautifulSoup object

    Args:
        soup (bs4.BeautifulSoup): BeautifulSoup object

    Returns:
        list: list of jobs as dictionaries
    """
    li_job_class = "separator-top"
    div_job_class = "row-fluid job-details pointer"
    job_web_elements = soup.find_all("li", {"class": li_job_class})
    jobs = []
    for job in job_web_elements:
        details = job.get_text().split('\n')
        details = [d.strip() for d in details if len(d) > 0]
        if len(details) > 4:
            title = details[0]
            company = details[1]
            location = details[2]
            rank = details[4]
            job_link_div_class = "bloc-right"
            link = job.find("div", {"class": job_link_div_class}).get("onclick",default=pd.NA).replace(";", "=").split('=')[1].strip("' ")
            jobs.append({"title": title,
                         "company": company,
                         "location": location,
                         "rank": rank,
                         "link": link
                        })
    return jobs

soup = make_soup()
jobs = scarpe_jobs(soup)
jobs_pprint = json.dumps(jobs, indent=1, allow_nan=True, ensure_ascii=False)
print(jobs_pprint)
with open("jobs1.json", 'a+') as f:
    f.write(jobs_pprint)