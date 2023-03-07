from bs4 import BeautifulSoup as bs
import requests
import pandas as pd
import datetime as dt
import os.path as path
from time import sleep
import json

def make_soup_of_page(limit=50, page=1, up_to_page=False):
    """Generate BeautifulSoup object for the local variable 'url'

    Args:
        limit (int, optional): number of results per page. Defaults to 50.
        page (int, optional): number of pages. Defaults to 1.
        ip_to_page (bool, optional): scrape jobs from the start up to the specified page. Defaults to False.

    Returns:
        bs4.BeautifulSoup: BeautifulSoup object
    """
    # get the user agent from 'edge://version/' in Microsoft Edge 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/102.0.5005.124 Safari/537.36 Edg/102.0.1245.44'}
    markup = ""
    if up_to_page:
        for p in range(page):
            start = p * limit
            url = "https://www.emploitic.com/offres-d-emploi?limit={0}&start={1}".format(limit, start)
            sleep(5)
            response = requests.get(url, headers=headers)
            markup += response.text
    
    else:        
        start = (page-1) * limit
        url = "https://www.emploitic.com/offres-d-emploi?limit={0}&start={1}".format(limit, start)
        response = requests.get(url, headers=headers, timeout=10)
        markup = response.text
    
    soup = bs(markup, 'html.parser')
    return soup

def make_soup_from_start(start=0, limit=50):
    """Generate BeautifulSoup object for the local variable 'url'

    Args:
        limit (int, optional): number of results per page. Defaults to 50.
        start (int, optional): number of offers to skip. Defaults to 0.

    Returns:
        bs4.BeautifulSoup: BeautifulSoup object
    """
    # get the user agent from 'edge://version/' in Microsoft Edge 
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.61'}
    url = "https://www.emploitic.com/offres-d-emploi?limit={0}&start={1}".format(limit, start)
    response = requests.get(url, headers=headers)
    markup = response.text
    
    soup = bs(markup, 'html.parser')
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
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/109.0.0.0 Safari/537.36 Edg/109.0.1518.61'}
    for job in job_web_elements:
        # Get initial details from job card
        initial_details = job.get_text().split('\n')
        initial_details = [d.strip() for d in initial_details if len(d) > 0]
        if len(initial_details) > 4:
            job_link_div_class = "bloc-right"
            job_link = job.find("div", {"class": job_link_div_class}).get("onclick",default=pd.NA).replace(";", "=").split('=')[1].strip("' ")
            job_details = {
            "title": initial_details[0],
            "company": initial_details[1],
            "Lieu de travail": initial_details[2], # location can be incomplete in this stage, gets updated from details page if found
            "publish_date": initial_details[3],
            "Niveau de poste": initial_details[4]
            }
            sleep(7)
            # Look for more details in job details page
            response = requests.get(job_link, headers=headers, timeout=30)
            job_page_soup = bs(response.text, 'html.parser')
            # 2 forms of job details page
            job_details_div_class_1 = "spaced-top row-fluid"
            job_details_div_class_2 = "span12 spaced-bot apply-info"
            # Get form 1
            job_details_div_1 = job_page_soup.find("div", {"class": job_details_div_class_1})
            # 2 different class values for form 1
            if job_details_div_1:
                job_details_text_1 = job_details_div_1.get_text()
            else:
                job_details_div_class_1_alt = "spaced-top row-fluid criterias-top"
                job_details_div_1_alt = job_page_soup.find("div", {"class": job_details_div_class_1_alt})
                # Skip if neither classes exist
                if not job_details_div_1_alt:
                    continue
                job_details_text_1 = job_details_div_1_alt.get_text()
            
            # Get form 2
            job_details_div_2 = job_page_soup.find("div", {"class": job_details_div_class_2})
            # Get text from either forms
            job_details_text_2 = job_details_div_2.get_text() if job_details_div_2 else ""
            more_job_details = job_details_text_2.split('\n') if job_details_text_2 else job_details_text_1.split('\n')
            # Clean text
            more_job_details = [d.strip() for d in more_job_details if len(d) > 0]
            more_job_details = {k:v for k, v in zip(more_job_details[::2], more_job_details[1::2]) if k != "Niveau de poste"}
            # concatenate details dicts
            job_details = {**job_details, **more_job_details}
            # add link and scraped_time keys
            job_details["scraped_time"] = dt.datetime.today()
            job_details["link"] = job_link
            
            # reformat dates
            today = dt.date.today()
            publish_date = job_details["publish_date"]
            if publish_date == "Aujourd'hui":
                job_details["publish_date"] = today.strftime("%d %B %Y")
            elif publish_date == "Hier":
                job_details["publish_date"] = (today - dt.timedelta(days=1)).strftime("%d %B %Y")
            elif publish_date == "Avant hier":
                job_details["publish_date"] = (today - dt.timedelta(days=2)).strftime("%d %B %Y")
            elif len(publish_date.split()) < 3:
                job_details["publish_date"] = publish_date + today.strftime(" %Y")
            
            # add current year to year'less' dates
            if "Date d'expiration" in job_details:
                expiry_date = job_details["Date d'expiration"]
                if len(expiry_date.split()) < 3:
                    expiry_date = expiry_date + today.strftime(" %Y")
                    job_details["Date d'expiration"] = expiry_date
                
            print(json.dumps(job_details, indent=1, allow_nan=True, ensure_ascii=False, default=str))
            print(f"{job_web_elements.index(job) + 1} / {len(job_web_elements)}")
            
            jobs.append(job_details)
    return jobs

def combine_unique(df1: pd.DataFrame, df2: pd.DataFrame, *dfs: list[pd.DataFrame]) -> pd.DataFrame:
    """Concatenate two or more dataframes keeping only unique records resetting the index

    Args:
        df1 (list[pandas.DataFrame]): First DataFrame
        df2 (pandas.DataFrame): Second DataFrame
        dfs (pandas.DataFrame): DataFrames to concatenate
    
    Returns:
        pands.DataFrame: DataFrame containing concatenated dataframes
    """        
    in_dfs = [df1, df2] + list(dfs)
    df = pd.concat(in_dfs, ignore_index=True)
    return df.drop_duplicates(ignore_index=True)

def jobs_to_csv(jobs, filename, mode='a'):
    """Save job data to a csv file

    Args:
        jobs (list(dict)): list of jobs as dictionaries
        filename (str): csv filename
        mode (str, optional): file access mode. Defaults to 'a+'.
    """    
    new_jobs = pd.DataFrame(jobs)
    if 'a' in mode and path.exists(filename):
            existing_jobs = pd.read_csv(filename)
            data = combine_unique(new_jobs, existing_jobs)
            data.to_csv(filename, mode='w', index=False)
            return
    
    new_jobs.to_csv(filename, mode=mode, index=False)

def jobs_to_json(jobs, filename, mode='a+'):
    """Save job data to a json file

    Args:
        jobs (list(dict)): list of jobs as dictionaries
        filename (str): json filename
        mode (str, optional): file access mode. Defaults to 'a+'.
    """    
    new_jobs = pd.DataFrame(jobs)
    if 'a' in mode and path.exists(filename):
            # with open(filename) as f:
            #     existing_data = json.load(f)
            
        
        existing_jobs = pd.read_json(filename, encoding='utf-8')
        data = combine_unique(new_jobs, existing_jobs)
        data.to_json(filename, indent=1, force_ascii=False, orient="records")
        return
            
        # with open(filename, "w") as f:
        #     data = existing_data + jobs
        #     json.dump(data, f, indent=1, allow_nan=True, ensure_ascii=False)
        # return
            
    
    new_jobs.to_json(filename, indent=1, force_ascii=False, orient="records")
    # with open(filename, mode) as f:
    #     json.dump(jobs, f, indent=1, allow_nan=True, ensure_ascii=False)
    
if __name__=="__main__":
    soup = make_soup_from_start(start=1800, limit=82)
    jobs = scrape_jobs(soup)
    json_filename = "job_test.json"
    csv_filename = "job_test.csv"
    
    print(f"Saving job data to json file {json_filename}...")
    jobs_to_json(jobs, json_filename)
    print("Done", end="\n")
    print(f"Saving job data to csv file {csv_filename}...")
    jobs_to_csv(jobs, csv_filename)
    print("Done")
    