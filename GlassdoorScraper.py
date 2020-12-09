from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from pathlib import Path
import mysql.connector
import pandas as pd
import numpy as np
import argparse
import logging
import random
import json
import time
import csv
import sys
import re
import requests

logging.basicConfig(filename="glassdoor_scraping.log",
                    format='%(asctime)s-%(levelname)s-FUNC:%(funcName)s-LINE:%(lineno)d-%(message)s',
                    level=logging.INFO)

BASE_URL = "https://www.glassdoor.com/Job/palo-alto-data-scientist-jobs-SRCH_IL.0,9_IC1147434_KO10,24.htm"


def retry(func):
    """
    Wrap any function that has to interact with the web-site.
    Handles  selenium's StaleElementExceptions and NoSuchElementException
    """

    def func_wrapper(*args, **kwargs):
        try_number = 1
        while try_number <= 3:
            logging.info(f"Executing {func.__name__}, try number: {try_number}")
            try:
                return func(*args, **kwargs)
            except TimeoutException:
                logging.warning(f"TimeoutException occurred when executing the function: {func.__name__}")
            except StaleElementReferenceException:
                logging.warning(f"StaleElementReferenceException when executing the function: {func.__name__}")
            except Exception as e:
                logging.warning(f"Exception was thrown when executing the function {func.__name__}\n"
                                f"{e}")

            try_number += 1
        else:
            logging.error(f"Was trying to execute {func.__name__} {try_number} times but FAILED")
            raise ValueError("Apparently no such element on page or something is missing")

    return func_wrapper


class ScraperManager:

    def __init__(self, path, driver_filename, job_title, job_location, rating_filter, number_of_jobs, headless):
        """
        Construct ScraperManager instance with user CLI arguments
        """
        logging.info(f"Creating ScraperManager with the following parameters:\n"
                     f"path: {path}, driver: {driver_filename}, job: {job_title},\n"
                     f"loc: {job_location}, rating: {rating_filter}, jobs: {number_of_jobs}")

        self.jobs_data = {'Company': [],
                          'City': [],
                          'State': [],
                          'Title': [],
                          'Min Salary': [],
                          'Max Salary': [],
                          'Min Company Size': [],
                          'Max Company Size': [],
                          'Revenue': [],
                          'Industry': []}

        self._non_rating_keys = ['Company',
                                 'City', 'State',
                                 'Title',
                                 'Min Salary', 'Max Salary',
                                 'Min Company Size', 'Max Company Size',
                                 'Revenue', 'Industry']

        self._title = job_title
        self._location = job_location
        self._res_path = path
        self.rating_filter = rating_filter
        self._headless = headless

        self._driver_path = driver_filename
        self.driver = self._init_driver()
        self._input_search_params()
        time.sleep(random.uniform(0.8, 2.5))
        self._total_jobs_found = self._get_amount(of_what='jobs')
        self._total_pages = self._get_amount(of_what='pages')
        if number_of_jobs is not None:
            self._num_of_jobs = min(number_of_jobs, self._total_jobs_found)
        else:
            self._num_of_jobs = self._total_jobs_found

        logging.info(f"Successfully constructed ScraperManager instance\n"
                     f"Search total pages: {self._total_pages},\n"
                     f"Search total jobs: {self._num_of_jobs}\n")

        self._df = pd.DataFrame()

    @property
    def number_of_pages(self):
        """
        Getter function - get total pages found
        """
        return self._total_pages

    @property
    def num_of_jobs(self):
        """
        Getter function - get number of jobs to scrap
        """
        return self._num_of_jobs

    def _init_driver(self) -> webdriver.Chrome:
        """
        Initiating Chromedriver instance for interacting with the website
        Being used as soon as ScraperManager object created (in the __init__ function)
        """
        logging.info("Initiating Chromedriver instance")

        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        if self._headless:
            options.add_argument('--headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver_path = Path.cwd().joinpath(self._driver_path)
        try:
            driver = webdriver.Chrome(executable_path=str(driver_path), options=options)
        except WebDriverException:
            raise IOError("Make sure you are using proper chrome driver\n"
                          "and/or you've inserted its name properly (including the file suffix if needed)")

        driver.get(BASE_URL)

        logging.info("Successfully created Chromedriver instance")

        self._bypass_login(driver)

        return driver

    @staticmethod
    def _bypass_login(driver):
        """
        Bypass the signup/login pop-up (if present)
        Used as part of the Chromedriver initialization (in the _init_driver() function)
        """
        logging.info("Bypassing the 'sign in' pop up")

        try:
            driver.find_element_by_class_name("selected").click()
        except ElementClickInterceptedException:
            pass

        try:
            driver.find_element_by_class_name("modal_closeIcon").click()
        except NoSuchElementException:
            pass

        logging.info("Successfully bypassed the pop up")

    def _input_search_params(self):
        """
        Establishes website interaction for inserting the user's search parameters
        Being used in the __init__() function
        """
        logging.info(f"Inserting search parameters: \n"
                     f"job: {self._title}, location: {self._location}")

        self.driver.find_element_by_xpath('.//input[@name="sc.keyword"]').clear()
        self.driver.find_element_by_xpath('.//input[@name="sc.keyword"]').send_keys(self._title)

        time.sleep(random.uniform(1, 1.5))

        self.driver.find_element_by_xpath('.//input[@id="sc.location"]').clear()
        self.driver.find_element_by_xpath('.//input[@id="sc.location"]').send_keys(self._location)

        time.sleep(random.uniform(1, 1.5))
        self.driver.find_element_by_xpath('.//button[@id="HeroSearchButton"]').click()

        logging.info("Successfully inserted search parameters")

    @retry
    def _get_amount(self, of_what) -> int:
        """
        Scrap the website for finding the total amount of jobs and pages
        matches the user's search criteria
        """
        if of_what == 'jobs':
            pattern = r"(^\d+)"
            xpath = './/div[@data-test="jobCount-H1title"]'

        elif of_what == 'pages':
            pattern = r"(\d+$)"
            xpath = './/div[@data-test="page-x-of-y"]'

        wait = WebDriverWait(self.driver, 2)
        raw_number = wait.until(EC.presence_of_element_located(
            (By.XPATH, xpath))).text

        match = re.search(pattern, raw_number)

        if match is None:
            logging.warning("Search criteria doesn't satisfied")
            raise StopIteration("Your search criteria doesn't satisfied\n"
                                "Consider changing it")

        number = int(match.group())

        return number

    def find_jobs_on_page(self) -> list:
        """
        Gets all the jobs listing in a certain search page
        Used in the main() function
        """
        logging.debug("Searching for jobs in page")
        jobs = self.driver.find_elements_by_class_name("jl")
        logging.debug(f"Found overall {len(jobs)} jobs on page")

        return jobs

    @retry
    def click_tab(self, tab_name):
        """
        Interacts with the website for clicking on given tab_name
        :param tab_name: str - Tab name to click on
        """
        if tab_name.lower() == 'company':
            xpath = './/div[@class="tab" and @data-tab-type="overview"]'
        elif tab_name.lower() == 'rating':
            xpath = './/div[@class="tab" and @data-tab-type="rating"]'
        elif tab_name.lower() == 'next':
            xpath = './/a[@data-test="pagination-next"]'
        else:
            raise ValueError("tab_name should be among [company, rating, next]")

        wait = WebDriverWait(self.driver, 2)
        wait.until(EC.presence_of_element_located(
            (By.XPATH, xpath))).click()

        time.sleep(random.uniform(0.8, 2.2))

    def fill_dict(self, job_obj):
        """
        Fill the jobs_data data structure with the job information in job_obj
        Being used in main()
        :param job_obj: Job instance
        """
        logging.info("Filling the jobs info data structure")

        self.jobs_data['Company'].append(job_obj.company_name)
        self.jobs_data['City'].append(job_obj.job_city)
        self.jobs_data['State'].append(job_obj.job_state)
        self.jobs_data['Title'].append(job_obj.job_title)
        self.jobs_data['Min Salary'].append(job_obj.job_min_salary)
        self.jobs_data['Max Salary'].append(job_obj.job_max_salary)
        self.jobs_data['Min Company Size'].append(job_obj.min_company_size)
        self.jobs_data['Max Company Size'].append(job_obj.max_company_size)
        self.jobs_data['Revenue'].append(job_obj.company_revenue)
        self.jobs_data['Industry'].append(job_obj.company_industry)

        logging.info("Done filling the jobs info data structure")

    def update_nans(self):
        """
        This function executed if certain job has no information on its company rating!
        Updates the jobs_data data structure with nans where needed.
        Being used in main()
        """
        for key in self.jobs_data.keys():
            if key not in self._non_rating_keys:
                self.jobs_data[key].append(np.nan)

    def update_jobs_data(self, rating_dict):
        """
        Updates the jobs_data data structure according to the job's ratings scores.
        If the jobs_data doesn't already contains certain rating field,
        create new key for it and use pad_with_nans() for inserting NaNs at the beginning.
        Used in main()
        """

        for rating_label, score in rating_dict.items():
            if rating_label in self.jobs_data:
                self.jobs_data[rating_label].append(score)
            else:
                self.jobs_data[rating_label] = []
                self.pad_with_nans(rating_label)
                self.jobs_data[rating_label].append(score)

        self.update_nans_for_existing(rating_dict)

    def pad_with_nans(self, field):
        """
        Used by update_jobs_data() for padding the beginning of a given list with NaNs
        """
        for company in self.jobs_data['Company'][:-1]:
            self.jobs_data[field].append(np.nan)

    def update_nans_for_existing(self, rating_dict):
        """
        Append NaNs to a given dictionary key's list.
        Being used by update_jobs_data()
        """
        for field, list_of_vals in self.jobs_data.items():
            if field not in rating_dict and field not in self._non_rating_keys:
                self.jobs_data[field].append(np.nan)

    def create_dataframe(self):
        """
        Create Pandas DataFrame out of the scraping results
        Being used in main()
        """

        self._df = pd.DataFrame(self.jobs_data)

    def save_results(self):
        """
        After creating pandas DataFrame, save it to a CSV file
        """
        self._df.to_csv(self._res_path)


class Job:

    def __init__(self, job_tag, driver):
        """
        Constructing Job instance
        Holds information for a certain job
        :param job_tag: HTML tag
        """
        self._job_tag = job_tag
        self._driver = driver

        self.company_name = np.nan
        self.job_city = np.nan
        self.job_state = np.nan
        self.job_title = np.nan
        self.job_min_salary = np.nan
        self.job_max_salary = np.nan
        self.min_company_size = np.nan
        self.max_company_size = np.nan
        self.company_industry = np.nan
        self.company_revenue = np.nan
        self.overall_rating = np.nan
        self.ratings = {}

    @retry
    def click(self):
        """
        Interact with the website for clicking on this specific job button
        Used in main()
        """
        # self._job_tag.click()
        self._job_tag.find_element_by_class_name("jobInfoItem").click()

    @retry
    def get_common_params(self):
        """
        Extract common job parameters: company name, city, state, job title and salary
        Used in main() function
        """
        logging.info("Extracting job information")

        self.company_name = self._job_tag.find_element_by_class_name("jobHeader").text
        job_location = self._job_tag.find_element_by_class_name('loc').text.split(',')
        self.job_city = job_location[0]
        self.job_state = job_location[1] if len(job_location) > 1 else np.nan
        self.job_title = self._job_tag.find_element_by_class_name('jobTitle').text

        self._get_salary_range()

        try:
            self.overall_rating = float(self._job_tag.find_element_by_class_name('compactStars').text)
        except NoSuchElementException:
            pass

        logging.info(f"Successfully extracted job's information:\n"
                     f"Job: {self.job_title}, Company name: {self.company_name}\n"
                     f"City: {self.job_city}, State: {self.job_state}\n"
                     f"Minimum Salary: {self.job_min_salary}, Maximum Salary: {self.job_max_salary}")

    def _get_salary_range(self):
        """
        Scrap the job instance for salary range (if present)
        Being used in get_common_params() function
        """

        try:
            job_salary_estim = self._job_tag.find_element_by_class_name('salaryEstimate').text
            salary_range = re.findall(r"\$(\d+\w*)\S+\$(\d+\w*)", str(job_salary_estim))
            self.job_min_salary = salary_range[0][0]
            self.job_max_salary = salary_range[0][1]
        except NoSuchElementException:
            pass

    @retry
    def get_non_common_params(self):
        """
        Scrap the job web-page and extract additional information that doesn't necessarily
        appears in other job web-page.
        Used in main()
        """
        logging.info("Extracting more Job's features")
        try:
            company_size = self._driver.find_element_by_xpath(
                './/div[@class="infoEntity"]/label[text()="Size"]/following-sibling::*').text

            pattern = r"(\d+)"
            size_range = re.findall(pattern, str(company_size))
            self.min_company_size = size_range[0]
            self.max_company_size = size_range[1]
        except NoSuchElementException:
            pass
        except Exception as e:
            logging.warning(f"Received exception: {e}")
            self.min_company_size = '10000'
            self.max_company_size = '100000'

        try:
            self.company_industry = self._driver.find_element_by_xpath(
                './/div[@class="infoEntity"]/label[text()="Industry"]/following-sibling::*').text
        except NoSuchElementException:
            pass

        try:
            self.company_revenue = self._driver.find_element_by_xpath(
                './/div[@class="infoEntity"]/label[text()="Revenue"]/following-sibling::*').text
        except NoSuchElementException:
            pass

        logging.info(f"Successfully extracted additional job's info\n"
                     f"Company size: {self.min_company_size} - {self.max_company_size}\n"
                     f"Industry: {self.company_industry}\n"
                     f"Revenue: {self.company_revenue}")

    @retry
    def get_ratings_scores(self):
        """
        This function execute as long as the job web-page has "Rating" tab.
        Scraps for the ratings fields and their scores anc calculates the overall rating.
        Eventually, stores all the information in ratings_dict
        """
        logging.info("Scraping for Ratings scores")

        raw_rating_parameters = self._driver.find_elements_by_xpath(
            './/div[@class="stars"]/ul/li/span[@class="ratingType"]')

        rating_parameters = tuple(map(lambda item: item.text, raw_rating_parameters))

        raw_rating_values = self._driver.find_elements_by_xpath(
            './/div[@class="stars"]/ul/li/span[@class="ratingValue"]/span[@class="ratingNum"]')

        rating_values = tuple(map(lambda item: float(item.text), raw_rating_values))

        self.ratings = dict(zip(rating_parameters, rating_values))
        if len(self.ratings):
            overall_rating = float(round(sum(self.ratings.values()) / len(self.ratings), 2))

            self.ratings['Overall Rating'] = overall_rating

        logging.info(f"Done scraping for ratings\n"
                     f"The Ratings scores are: {self.ratings}")


class DatabaseManager:

    @staticmethod
    def construct_create_table_commands():
        """
        Construct mySQL commands for creating the tables in the database
        """
        logging.info("Constructing mySQL commands for creating tables")
        crate_table_commands = {}

        job_ratings = '''CREATE TABLE Ratings(idRatings INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                              Culture_values FLOAT, 
                                              Diversity_inclusion FLOAT,
                                              Work_life_balance FLOAT,
                                              Senior_management FLOAT, 
                                              Benefits FLOAT,
                                              Career_opportunities FLOAT, 
                                              Overall_rating FLOAT)'''

        crate_table_commands["Ratings"] = job_ratings

        company = '''
        CREATE TABLE Company(idCompany INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                             Company_name VARCHAR(45) NOT NULL, 
                             Min_Size INT,
                             Max_Size INT, 
                             Revenue_est TEXT, 
                             Industry VARCHAR(50), 
                             idRatings INT, 
                             FOREIGN KEY(idRatings) REFERENCES Ratings(idRatings))'''

        crate_table_commands["Company"] = company

        company_stock_details = '''
               CREATE TABLE Company_stock_details(idCompany_stock_details INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                                    Stock_price FLOAT, 
                                    Market_cap FLOAT,
                                    Currency VARCHAR(10), 
                                    Website TEXT, 
                                    FOREIGN KEY(idCompany) REFERENCES Company(idCompany))'''

        crate_table_commands["Company_stock_details"] = company_stock_details

        job_post = '''
        CREATE TABLE Job_post(idJob_post INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                              Title TEXT NOT NULL, 
                              Min_Salary VARCHAR(10),
                              Max_Salary VARCHAR(10), 
                              idCompany INT, 
                              FOREIGN KEY (idCompany) REFERENCES Company(idCompany))'''

        crate_table_commands["Job_post"] = job_post

        job_location = '''
        CREATE TABLE Job_location(idJob_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                                  City VARCHAR(45), 
                                  State VARCHAR(10))'''

        crate_table_commands["Job_location"] = job_location

        job_post_location = '''
        CREATE TABLE Job_post_location(idJob_post_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY,  
                                       idJob_post INT,
                                       idJob_location INT,
                                       FOREIGN KEY (idJob_post) REFERENCES Job_post(idJob_post),
                                       FOREIGN KEY (idJob_location) REFERENCES Job_location(idJob_location))'''

        crate_table_commands["Job_post_location"] = job_post_location

        logging.info("Done constructing tables commands")

        return crate_table_commands

    @staticmethod
    def create_database(host, username, password, db_name):
        """
        Create new mySQL database (if not exists yet)
        """
        logging.info("Establishing mySQL connection")
        my_db = mysql.connector.connect(host=host, user=username, passwd=password)
        cursor = my_db.cursor()
        logging.info("Connection established successfully")

        cursor.execute("SHOW DATABASES")
        databases = cursor.fetchall()
        if (db_name.lower(),) not in databases:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
            my_db.commit()
            cursor.execute("SHOW DATABASES")
            databases = cursor.fetchall()
            if (db_name.lower(),) in databases:
                logging.info(f"Successfully created {db_name} Database")
            else:
                logging.error("Could not create Database")

            cursor.close()
            my_db.close()
            logging.info("mySQL connection closed")

    @staticmethod
    def create_tables(host, username, password, db_name, create_table_commands):
        """
        Based on the returned value from construct_create_table_commands() function,
        execute mySQL commands for creating the tables inside the db_name database
        :param create_table_commands - Dict with table names as keys, and mySQL 'create table'
                                       command as values
        """
        logging.info("Establishing mySQL connection")
        my_db = mysql.connector.connect(host=host, user=username, passwd=password, database=db_name)
        cursor = my_db.cursor()
        logging.info("Connection established successfully")

        cursor.execute(f"SHOW TABLES IN {db_name}")
        existing_tables = cursor.fetchall()
        for table_name, crate_command in create_table_commands.items():
            if (table_name.lower(),) not in existing_tables:
                cursor.execute(crate_command)
                logging.info(f"Creating {table_name} table")
                my_db.commit()
                logging.info(f"{table_name} created successfully")

        cursor.close()
        my_db.close()
        logging.info("mySQL connection closed")

    @staticmethod
    def insert_values(host, username, password, db_name, data_file, num_of_jobs):
        """
        Reads data from a given data_file and inserts its values to the tables in db_name
        """
        logging.info("Establishing mySQL connection")
        my_db = mysql.connector.connect(host=host, user=username, passwd=password, database=db_name)
        cursor = my_db.cursor()
        logging.info("Connection established successfully")

        # Extracting relevant data from the csv file
        with open(fr"{data_file}", 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)

            for line_num, line in enumerate(reader):
                line = DatabaseManager.replace_nans(line)
                ratings_data = line[11:]

                cursor.execute('''INSERT INTO Ratings (Culture_values, 
                                                       Diversity_inclusion,
                                                       Work_life_balance,  
                                                       Senior_management,
                                                       Benefits,
                                                       Career_opportunities,
                                                       Overall_rating)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s )''', ratings_data)

                idRatings = cursor.lastrowid

                cursor.execute('''INSERT INTO Company (Company_name,
                                                       Min_Size, 
                                                       Max_Size, 
                                                       Revenue_est, 
                                                       Industry, 
                                                       idRatings
                                                       ) 
                                  VALUES (%s, %s, %s, %s, %s, %s)''',
                               (line[1], line[7], line[8], line[9], line[10], idRatings))

                idCompany = cursor.lastrowid

                cursor.execute('''INSERT INTO Job_post (Title, 
                                                        Min_Salary, 
                                                        Max_Salary, 
                                                        idCompany)
                                  VALUES (%s, %s, %s, %s)''', (line[4], line[5], line[6], idCompany))

                idJob_post = cursor.lastrowid

                cursor.execute('''INSERT INTO Job_location (City, State) 
                                  VALUES (%s, %s)''', (line[2], line[3]))

                idJob_location = cursor.lastrowid

                cursor.execute('''INSERT INTO Job_post_location (idJob_post, idJob_location) 
                                  VALUES (%s, %s)''', (idJob_post, idJob_location))

                if num_of_jobs <= 10:
                    logging.info("Committing changes")
                    my_db.commit()
                    logging.info("Done committing changes")
                elif num_of_jobs % 15 == 0:
                    logging.info("Committing changes")
                    my_db.commit()
                    logging.info("Done committing changes")

        my_db.commit()
        cursor.close()
        my_db.close()
        logging.info("Connection established successfully")

    @staticmethod
    def replace_nans(val_list):
        """
        Replace missing values with nans.
        Making it easier for the mySQL to handle with.
        An auxiliary function to insert_values()
        """
        fixed_list = [item if item != '' else None for item in val_list]

        return fixed_list


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
    """

    usage = """%(prog)s [-h] [-l] [-jt] [-n] [--db-username/-dbu] [--db-password/-dbp] [--db-name/-dbn] [
    --headless/-hl] [--verbose/-v] """

    parser = argparse.ArgumentParser(description=desc,
                                     prog='GlassdoorScraper.py',
                                     usage=usage,
                                     epilog="Make sure to have the chromedriver at the exact same "
                                            "directory of this script!",
                                     fromfile_prefix_chars='@')

    parser.add_argument('-l', '--location', action='store', default=' ', type=str,
                        help="Job Location")

    parser.add_argument('-jt', '--job_type', action='store', default=' ', type=str,
                        help='Job Title')

    parser.add_argument('-n', '--number_of_jobs' , action='store', type=int, default=None,
                        help="Amount of jobs to scrap, "
                             "if you'll insert 'n' greater than amount of jobs found\n"
                             "the scraper will simply scrap whatever it founds, obviously")

    parser.add_argument('-rt', '--rating_threshold', action='store', type=float, default=0,
                        help="Get jobs info above certain overall rating threshold")

    parser.add_argument('-dbu', '--db-username', action='store', type=str, required=True,
                        help="Your database user name",
                        metavar="DB_USERNAME")

    parser.add_argument('-dbp', '--db-password', action='store', required=True, type=str,
                        help="Your database login password",
                        metavar="DB_PASSWORD")

    parser.add_argument('-dbn', '--db-name', action='store', type=str, default="GlassdoorDB",
                        help="Choose database name as you wish (optional)",
                        metavar="DB_NAME")

    parser.add_argument("-hl", "--headless", action='store_true',
                        help="Choose whether or not displaying the google chrome window while scraping")

    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Optional - Choose either printing output to std or not")

    args = parser.parse_args()

    # args = parser.parse_args(['res.csv', 'chromedriver.exe', '-l', 'San Francisco', '-jt', 'data scientist',
    #                           '-n', '10', '--verbose', '--db-username', 'root', '--db-password', 'Ihaawsmon6am',
    #                           '--db-name', "GlassdoorDB"])

    # args = parser.parse_args(['res.csv', 'chromedriver.exe', '-l', 'San Francisco', '-n', '50',
    #                           '--db-username', 'root', '--db-password', 'Ihaawsmon6am',
    #                           '--db-name', "GlassdoorDB"])

    return args


def main():
    """
    The scarping begins here!
    Uses two separate objects: ScraperManager and Job
    ScraperManager in charge of interacting with the website,
    whereas Job extract information regarding specific job
    """
    args = parse_args()

    with open('config.json') as config_file:
        configurations = json.load(config_file)

    chromedriver_path = configurations['chromedriver']
    results_path = configurations['results_path']

    try:
        sm = ScraperManager(path=results_path, driver_filename=chromedriver_path,
                            job_title=args.job_type, job_location=args.location,
                            rating_filter=args.rating_threshold, number_of_jobs=args.number_of_jobs,
                            headless=args.headless)
    except IOError as e:
        logging.error(f"Failed due to: {e}")
        sys.exit(1)
    except StopIteration as e:
        logging.error(f"Failed due to: {e}")
        sys.exit(1)
    except Exception as e:
        print(e)
        logging.error(f"Failed due to: {e}")
        sys.exit(1)

    job_id = 0
    while job_id < sm.num_of_jobs:

        jobs = sm.find_jobs_on_page()

        for job in jobs:

            job_obj = Job(job, sm.driver)
            job_obj.click()

            if job_id >= sm.num_of_jobs:
                break

            try:
                job_obj.get_common_params()
            except Exception as e:
                print(f"Failed due to {e}")
                sm.driver.close()
                sys.exit(1)

            if (job_obj.overall_rating >= args.rating_threshold) or \
                    (np.isnan(job_obj.overall_rating) and args.rating_threshold == 0):

                logging.info(f"Scraping job number {job_id + 1} out of {sm.num_of_jobs}")

                if args.verbose:
                    print(
                        f"@@ Scrap job number {job_id + 1} out of {sm.num_of_jobs}: {(job_id + 1) / sm.num_of_jobs:.2%} @@")
                    print(f"\tCompany Name: {job_obj.company_name}\n"
                          f"\tJob title: {job_obj.job_title}\n"
                          f"\tCity: {job_obj.job_city}\n"
                          f"\tState: {job_obj.job_state}\n"
                          f"\tSalary: {job_obj.job_min_salary}-{job_obj.job_max_salary}")

                try:
                    sm.click_tab('company')
                except ValueError:
                    pass
                finally:
                    job_obj.get_non_common_params()

                if args.verbose:
                    print(f"\tCompany Size: {job_obj.min_company_size} to {job_obj.max_company_size}")
                    print(f"\tIndustry: {job_obj.company_industry}\n")

                sm.fill_dict(job_obj)

                logging.info("Generating the Ratings dict")
                try:
                    sm.click_tab('rating')
                except ValueError:
                    sm.update_nans()
                else:
                    job_obj.get_ratings_scores()
                    sm.update_jobs_data(job_obj.ratings)
                logging.info("Done generate the ratings dict")

                job_id += 1

        sm.click_tab('next')

    sm.create_dataframe()
    sm.save_results()
    logging.info("Done Scraping!")

    #### Creating the Database ###

    createTables_commands = DatabaseManager.construct_create_table_commands()

    db_host = configurations['database_host']
    db_username = args.db_username
    db_password = args.db_password
    db_name = args.db_name
    jobs = sm.num_of_jobs

    DatabaseManager.create_database(db_host, username=db_username, password=db_password, db_name=db_name)

    DatabaseManager.create_tables(db_host, username=db_username, password=db_password, db_name=db_name,
                                  create_table_commands=createTables_commands)

    DatabaseManager.insert_values(db_host, username=db_username, password=db_password, db_name=db_name,
                                  data_file=results_path, num_of_jobs=jobs)


if __name__ == "__main__":
    main()


