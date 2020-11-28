from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import WebDriverException, TimeoutException
from selenium.common.exceptions import StaleElementReferenceException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from pathlib import Path
import pandas as pd
import numpy as np
import argparse
import logging
import random
import time
import sys
import re

logging.basicConfig(filename="glassdoor_scraping.log",
                    format='%(asctime)s-%(levelname)s-FUNC:%(funcName)s-LINE:%(lineno)d-%(message)s',
                    level=logging.INFO)


def retry(func):
    """
    Wrap any function that has to interact with the web-site.
    Handles  selenium's StaleElementExceptions and NoSuchElementException
    """
    def func_wrapper(*args, **kwargs):
        try_number = 1
        while try_number <= 5:
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
            raise NoSuchElementException("Apparently no such element on page")

    return func_wrapper


class ScraperManager:

    def __init__(self, path, driver_filename, job_title, job_location, rating_filter, number_of_jobs):
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
        self._base_url = 'https://www.glassdoor.com/Job/palo-alto-data-scientist-jobs-SRCH_IL.0,9_IC1147434_KO10,24.htm'

        self._driver_path = driver_filename
        self.driver = self._init_driver()
        self._input_search_params()
        self._total_jobs_found = self._get_amount(of_what='jobs')
        self._total_pages = self._get_amount(of_what='pages')
        self._num_of_jobs = number_of_jobs if number_of_jobs < self._total_jobs_found else self._total_jobs_found

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
        # options.add_argument('--headless')
        options.add_experimental_option('excludeSwitches', ['enable-logging'])
        driver_path = Path.cwd().joinpath(self._driver_path)
        try:
            driver = webdriver.Chrome(executable_path=str(driver_path), options=options)
        except WebDriverException:
            raise IOError("Make sure you are using proper chrome driver\n"
                          "and/or you've inserted its name properly (including the file suffix if needed)")

        driver.get(self._base_url)

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

        wait = WebDriverWait(self.driver, 5)
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

        wait = WebDriverWait(self.driver, 3)
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
        self._job_tag.click()
        # self._job_tag.find_element_by_class_name("jobInfoItem").click()

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
        self.job_state = job_location[1]
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
            salary_range = re.findall(r"(\d+K)-\$(\d+K)", str(job_salary_estim))
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


def parse_args():
    """
    Parse CLI user arguments.
    Being used in main()
    """

    desc = """ You are about to scrap the GlassDoor jobs search platform.
    Before we begin, please make sure you have placed the Chrome driver within the same
    directory of the this script file.
    Chrome driver can be found at the following URL:
    https://chromedriver.storage.googleapis.com/index.html?path=87.0.4280.20/ 
    """

    parser = argparse.ArgumentParser(description=desc,
                                     prog='GlassdoorScraper.py',
                                     usage="%(prog)s results_filepath driver_filename [-h] [-l] [-jt] [-n] [-v]",
                                     epilog="Make sure to have the chromdriver at the exact same "
                                            "directory of this script!")

    parser.add_argument('res_path', action='store', type=str,
                        help="File path to save the results in")

    parser.add_argument('driver_filename', action='store', type=str,
                        help="File name of your Chrome Driver")

    parser.add_argument('--location', '-l', action='store', default=' ', type=str,
                        help="Job Location")

    parser.add_argument('--job_type', '-jt', action='store', default=' ', type=str,
                        help='Job Title')

    parser.add_argument('--number_of_jobs', '-n',  action='store', type=int, default=None,
                        help="Amount of jobs to scrap, "
                             "if you'll insert 'n' greater than amount of jobs found\n"
                             "the scraper will simply scrap whatever it founds, obviously")

    parser.add_argument('-rt', '--rating_threshold', action='store', type=float, default=0,
                        help="Get jobs info above certain overall rating threshold")

    parser.add_argument('--verbose', action='store_true',
                        help="Optional - Choose either printing output to std or not")

    args = parser.parse_args()
    # args = parser.parse_args(['res.csv', 'chromedriver.exe', '-l', 'San Francisco', '-jt', 'data scientist',
    #                           '-n', '10'])
    # args = parser.parse_args(['-h'])

    return args


def main():
    """
    The scarping begins here!
    Uses two separate objects: ScraperManager and Job
    ScraperManager in charge of interacting with the website,
    whereas Job extract information regarding specific job
    """
    args = parse_args()

    try:
        sm = ScraperManager(path=args.res_path, driver_filename=args.driver_filename,
                            job_title=args.job_type, job_location=args.location,
                            rating_filter=args.rating_threshold, number_of_jobs=args.number_of_jobs)
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

            job_obj.get_common_params()

            if job_obj.overall_rating >= args.rating_threshold:

                logging.info(f"Scraping job number {job_id+1} out of {sm.num_of_jobs}")

                try:
                    sm.click_tab('company')
                except NoSuchElementException:
                    pass
                finally:
                    job_obj.get_non_common_params()

                sm.fill_dict(job_obj)

                logging.info("Generating the Ratings dict")
                try:
                    sm.click_tab('rating')
                except NoSuchElementException:
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


if __name__ == "__main__":
    main()
