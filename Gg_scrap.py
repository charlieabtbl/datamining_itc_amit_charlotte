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
    """
    Parse JSON configuration file
    return: python dictionary
    """

    with open(Path.cwd().joinpath('config.json').as_posix()) as json_file:
        configurations = json.load(json_file)

    return configurations


def parse_args():
    """
    Parse CLI user arguments.
    Being used in main()
    """
    logger.info("Parse user CLI parameters")

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

    logger.info("Parsed successfully")

    return args


def main():
    """
    The scarping begins here!
    Uses function from the Scraping_handler module (imported above)
    Exceptions thrown in the craping_handler module module, bubbled and caught here
    """
    logger.info("Scraping began")
    args = parse_args()
    configurations = parse_json()
    try:
        general_data, company_tab_data, ratings_tab_data = do_scraping(args, configurations)
    except IOError as e:
        print(e)
        logger.error(f"===Something went wrong: {e}===")
        sys.exit(1)
    except ValueError as e:
        logger.error(f"===Something went wrong: {e}===")
        print(e)
        sys.exit(1)

    # Save Final Result
    try:
        create_csv_res_file(company_tab_data, general_data, ratings_tab_data,
                            configurations['Scraping']['results_path'])
    except Exception as e:
        print(e)
        logger.error(f"===Something went wrong: {e}===")
        sys.exit(1)

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
    # create_api_table()
    # insert_values(where_from='api')




