from selenium.common.exceptions import ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
from pathlib import Path
import pandas as pd
import requests
import argparse
import logging
import pathlib
import random
import time
import json
import sys
import csv
import re
import os
from Scraping_handler import *
from Results_handler import *
from Database import *


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('glassdoor_scraping.log', encoding='utf8')
file_handler.setLevel(logging.DEBUG)

file_format = logging.Formatter("'%(asctime)s - %(levelname)s - In: %(filename)s - LINE: %(lineno)d - %(funcName)s- "
                                "-%(message)s'")
file_handler.setFormatter(file_format)

logger.addHandler(file_handler)


def parse_json():

    with open(Path.cwd().joinpath('config.json').as_posix()) as json_file:
        configurations = json.load(json_file)

    return configurations


def get_chromedriver_path(configurations):

    # Get Driver Path
    driver_path = Path.cwd().joinpath(configurations['Scraping']['chromedriver'])
    if isinstance(driver_path, pathlib.WindowsPath):
        if len(driver_path.as_posix().split('.')) > 1:
            if driver_path.as_posix().split('.')[1] == 'exe':
                driver_path = driver_path.as_posix()
            else:
                raise IOError("Check your chromedriver file suffix")
        else:
            driver_path = driver_path.with_suffix(".exe").as_posix()
    else:
        driver_path = driver_path.as_posix()

    return driver_path


def parse_args():
    """
    Parse CLI user arguments.
    Being used in main()
    """

    desc = """ You are about to scrap the GlassDoor jobs search platform.
    Before we begin, please make sure you have placed the Chrome driver within the same
    directory of the this script file and that you've updated the config.json file accordingly.
    Chrome driver can be found at the following URL:
    https://chromedriver.storage.googleapis.com/index.html?path=87.0.4280.20/
    When passing the --api flag by its own, meaning you won't scrap Glassdoor, but only
    get data from the public API.
    ATTENTION: You should use this option (passing --api flag by its own) only if you certain
    your glassdoor database exists! 
    """

    usage = """%(prog)s [-h] [-l] [-jt] [-n] [--api] [--headless/-hl] [--verbose/-v] """

    parser = argparse.ArgumentParser(description=desc,
                                     prog='GlassdoorScraper.py',
                                     usage=usage,
                                     epilog="Make sure to have the chromedriver at the exact same "
                                            "directory of this script!",
                                     fromfile_prefix_chars='@')

    parser.add_argument('-l', '--location', action='store', default=False, type=str,
                        help="Job Location")

    parser.add_argument('-jt', '--job_type', action='store', default=False, type=str,
                        help='Job Title')

    parser.add_argument('-n', '--number_of_jobs', action='store', type=int, default=None,
                        help="Amount of jobs to scrap, "
                             "if you'll insert 'n' greater than amount of jobs found\n"
                             "the scraper will simply scrap whatever it founds, obviously")

    parser.add_argument('-rt', '--rating_threshold', action='store', type=float, default=0,
                        help="Get jobs info above certain overall rating threshold")

    parser.add_argument('--api', action='store_true',
                        help="Choose whether query also from a public Free Stocks API")

    parser.add_argument("-hl", "--headless", action='store_true',
                        help="Choose whether or not displaying the google chrome window while scraping")

    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Optional - Choose either printing output to std or not")

    args = parser.parse_args()

    return args


def main():

    general_data = []
    company_tab_data = []
    ratings_tab_data = []

    args = parse_args()
    configurations = parse_json()
    try:
        driver_path = get_chromedriver_path(configurations)
    except IOError as e:
        print(e)
        sys.exit(1)

    driver = initiate_driver(driver_path, args)
    try:
        jobs_found = get_num_of_matched_jobs(driver)
    except ValueError as e:
        print(e)
        driver.close()
        sys.exit(1)

    jobs_to_scrap = min(args.number_of_jobs, jobs_found) if args.number_of_jobs else jobs_found

    job_id = 1
    while len(general_data) < jobs_to_scrap:
        # Jobs on specific page
        jobs_list = driver.find_elements_by_class_name("jl")
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        bs_jobs_list = page_content.find_all("li", class_="jl")
        for idx, job in enumerate(jobs_list, start=1):
            if len(general_data) == jobs_to_scrap:
                break
            print("Job number: ", job_id)
            bs_job = bs_jobs_list[idx - 1]
            common_data = get_common_data(bs_job)
            general_data.append(common_data)

            # Click Job
            button = job.find_element_by_class_name("jobInfoItem")
            driver.execute_script("arguments[0].click();", button)

            time.sleep(random.uniform(1, 3))

            # Get Company Data
            job_company = get_company_data(driver)
            company_tab_data.append(job_company)

            # Get Rating Data
            overall_rating = 0
            job_ratings = get_rating_data(driver, bs_job)
            ratings_tab_data.append(job_ratings)

            if str(overall_rating) < str(args.rating_threshold):
                general_data.pop()
                ratings_tab_data.pop()
                company_tab_data.pop()

            else:
                job_id += 1

        # Click 'Next' Button
        xpath = './/a[@data-test="pagination-next"]'
        wait = WebDriverWait(driver, 3)
        next_button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        next_button.click()
        time.sleep(random.uniform(1, 2))

    driver.close()

    # Save Final Result
    save_to_csv('comp.csv', company_tab_data, ['Size', 'Founded', 'Type', 'Industry', 'Sector', 'Revenue'])

    save_to_csv('common.csv', general_data, ['Company_Name', 'Job_Title', 'City', 'State',
                                             'Min_Salary', 'Max_Salary'])

    save_to_csv('ratings.csv', ratings_tab_data, ['Overall', 'Culture & Values', 'Diversity & Inclusion',
                                                  'Work/Life Balance', 'Senior Management', 'Comp & Benefits',
                                                  'Career Opportunities'])

    merge_csvs(configurations['Scraping']['results_path'])

    # Create Database
    create_database(configurations)
    create_scarping_tables()
    insert_values()

    # Enrich with API
    if args.api:
        try:
            create_api_table()
            insert_values(where_from='api')
            print('Done')
        except Exception as e:
            print(e)


if __name__ == "__main__":
    main()




