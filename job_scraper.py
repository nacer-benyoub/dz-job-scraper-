import os.path as path
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

def scrape_jobs(soup):
    """Scrape job details from the BeautifulSoup object

    Args:
        soup (bs4.BeautifulSoup): BeautifulSoup object

    Returns:
        list: list of dictionaries
    """
    li_job_class = "separator-bot"
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

def jobs_to_csv(jobs, filename, mode='a'):
    """Save job data to a csv file

    Args:
        jobs (_type_): list of jobs as dictionaries
        filename (_type_): csv filename
        mode (str, optional): file access mode. Defaults to 'a+'.
    """    
    df = pd.DataFrame(jobs)
    print(df.head())
    df.to_csv(filename, mode=mode, index=False)

def jobs_to_json(jobs, filename, mode='a+'):
    """Save job data to a json file

    Args:
        jobs (_type_): list of jobs as dictionaries
        filename (_type_): json filename
        mode (str, optional): file access mode. Defaults to 'a+'.
    """    
    if path.exists(filename):
        with open(filename) as f:
            existing_data = json.load(f)
        
        if 'a' in mode and len(existing_data):
            with open(filename, "w") as f:
                data = existing_data + jobs
                json.dump(data, f, indent=1, allow_nan=True, ensure_ascii=False)
            return
            
    with open(filename, "w") as f:
        json.dump(jobs, f, indent=1, allow_nan=True, ensure_ascii=False)
    
if __name__=="__main__":
    soup = make_soup()
    jobs = scrape_jobs(soup)
    json_filename = "job_test.json"
    csv_filename = "job_test.csv"
    print(f"Saving job data to json file {json_filename}...")
    jobs_to_json(jobs, json_filename)
    print("Done", end="\n")
    print(f"Saving job data to json file {csv_filename}...")
    jobs_to_csv(jobs, csv_filename)
    print("Done")
    
    # add logic to add only new jobs and avoid redundancy