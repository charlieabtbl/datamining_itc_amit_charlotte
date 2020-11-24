from selenium.common.exceptions import NoSuchElementException, ElementClickInterceptedException
from selenium.common.exceptions import StaleElementReferenceException, TimeoutException
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
import pandas as pd
import numpy as np
import argparse
import random
import time
import math
import sys
import re
import os

MAX_JOBS = 50


def retry(func):
    def func_wrapper(*args, **kwargs):
        retries = 3
        while retries:
            try:
                func(*args, **kwargs)
                return
            except TimeoutException:
                raise NoSuchElementException("Apparently no such tab")
            except Exception as e:
                # print(e)
                retries -= 1
        else:
            raise NoSuchElementException("Apparently no such tab")

    return func_wrapper


class ScraperManager:

    def __init__(self, path, job_title='', job_location='', rating_filter=None, number_of_jobs=None,
                 page_num=1):

        self.jobs_data = {'Company': [],
                          'Location': [],
                          'Title': [],
                          'Salary': [],
                          'Company_Size': [],
                          'Revenue': [],
                          'Industry': []}

        self.filtered_dict = {}

        self._title = job_title
        self._location = job_location
        self._res_path = path
        self._page_num = page_num
        self._rating_filter = rating_filter
        self._base_url = 'https://www.glassdoor.com/Job/palo-alto-data-scientist-jobs-SRCH_IL.0,9_IC1147434_KO10,24.htm'

        self.driver = self._init_driver()
        self._input_search_params()
        self._total_jobs_found = self._get_jobs_amount()
        self._num_of_jobs = number_of_jobs if number_of_jobs < self._total_jobs_found else self._total_jobs_found
        self._number_of_pages = math.ceil(min(self._num_of_jobs, self._total_jobs_found) / 32)

        self._df = pd.DataFrame()

    @property
    def number_of_pages(self):
        return self._number_of_pages

    @property
    def page_num(self):
        return self._page_num

    @page_num.setter
    def page_num(self, value):
        self._page_num = value

    @property
    def num_of_jobs(self):
        return self._num_of_jobs

    def _init_driver(self) -> webdriver.Chrome:

        options = webdriver.ChromeOptions()
        options.add_argument('--ignore-certificate-errors')
        options.add_argument('--incognito')
        # options.add_argument('--headless')

        driver = webdriver.Chrome(executable_path='chromedriver.exe', options=options)
        driver.get(self._base_url)

        self._bypass_login(driver)

        return driver

    @staticmethod
    def _bypass_login(driver):

        try:
            driver.find_element_by_class_name("selected").click()
        except ElementClickInterceptedException:
            pass

        try:
            driver.find_element_by_class_name("modal_closeIcon").click()
        except NoSuchElementException:
            pass

    def _input_search_params(self):

        self.driver.find_element_by_xpath('.//input[@name="sc.keyword"]').clear()
        self.driver.find_element_by_xpath('.//input[@name="sc.keyword"]').send_keys(self._title)

        time.sleep(random.uniform(1, 1.5))

        self.driver.find_element_by_xpath('.//input[@id="sc.location"]').clear()
        self.driver.find_element_by_xpath('.//input[@id="sc.location"]').send_keys(self._location)

        time.sleep(random.uniform(1, 1.5))
        self.driver.find_element_by_xpath('.//button[@id="HeroSearchButton"]').click()

    def _get_jobs_amount(self) -> int:
        pattern = r"(^\d+)"
        match = re.search(pattern,
                          self.driver.find_element_by_xpath('.//div[@data-test="jobCount-H1title"]').text)

        if match is None:
            print("Search criteria doesn't satisfied")
            raise StopIteration("Your search criteria doesn't satisfied\n"
                                "Consider changing it")

        max_number_of_jobs = int(match.group())

        return max_number_of_jobs

    def find_num_of_jobs_on_page(self) -> list:

        jobs = self.driver.find_elements_by_class_name("jl")

        return jobs

    @retry
    def click_tab(self, tab_name):

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

        self.jobs_data['Company'].append(job_obj.company_name)
        self.jobs_data['Location'].append(job_obj.job_location)
        self.jobs_data['Title'].append(job_obj.job_title)
        self.jobs_data['Salary'].append(job_obj.job_salary)
        self.jobs_data['Company_Size'].append(job_obj.company_size)
        self.jobs_data['Revenue'].append(job_obj.company_revenue)
        self.jobs_data['Industry'].append(job_obj.company_industry)

    def update_nans(self):

        non_ratings_keys = ['Company',
                            'Location',
                            'Title',
                            'Salary',
                            'Company_Size',
                            'Revenue',
                            'Industry']

        for key in self.jobs_data.keys():
            if key not in non_ratings_keys:
                self.jobs_data[key].append(np.nan)

    def update_jobs_data(self, rating_dict):

        for rating_label, score in rating_dict.items():
            if rating_label in self.jobs_data:
                self.jobs_data[rating_label].append(score)
            else:
                self.jobs_data[rating_label] = []
                self.pad_with_nans(rating_label)
                self.jobs_data[rating_label].append(score)

        self.update_nans_for_existing(rating_dict)

    def pad_with_nans(self, field):

        for company in self.jobs_data['Company'][:-1]:
            self.jobs_data[field].append(np.nan)

    def update_nans_for_existing(self, rating_dict):

        non_ratings_keys = ['Company',
                            'Location',
                            'Title',
                            'Salary',
                            'Company_Size',
                            'Revenue',
                            'Industry']

        for field, list_of_vals in self.jobs_data.items():
            if field not in rating_dict and field not in non_ratings_keys:
                self.jobs_data[field].append(np.nan)

    def create_dataframe(self):

        self._df = pd.DataFrame(self.jobs_data)

    def save_results(self):

        self._df.to_csv(self._res_path)


class Job:
    _job_id = 1

    def __init__(self, job_tag, driver):
        self.id = Job._job_id
        Job._job_id += 1

        self._job_tag = job_tag
        self._driver = driver

        self.company_name = np.nan
        self.job_location = np.nan
        self.job_title = np.nan
        self.job_salary = np.nan
        self.company_size = np.nan
        self.company_industry = np.nan
        self.company_revenue = np.nan
        self.ratings = {}

    @retry
    def click(self):
        self._job_tag.click()
        # self._job_tag.find_element_by_class_name("jobInfoItem").click()

    def get_common_params(self):

        self.company_name = self._job_tag.find_element_by_class_name("jobHeader").text
        self.job_location = self._job_tag.find_element_by_class_name('loc').text
        self.job_title = self._job_tag.find_element_by_class_name('jobTitle').text
        try:
            self.job_salary = self._job_tag.find_element_by_class_name('salaryEstimate').text
        except NoSuchElementException:
            pass

    def get_non_common_params(self):

        try:
            self.company_size = self._driver.find_element_by_xpath(
                './/div[@class="infoEntity"]/label[text()="Size"]/following-sibling::*').text
        except NoSuchElementException:
            pass

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

    def get_ratings_scores(self):

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

    parser = argparse.ArgumentParser(prog='GlassDoorScraper.py',
                                     usage="%(prog)s [-h] [-l] [-jt] [-n]",
                                     epilog="If you'll insert 'n' greater than amount of jobs found\n"
                                            "the scraper will simply scrap whatever it found, obviously")

    parser.add_argument('-l', '--location', action='store', default=' ',
                        help="Job Location")

    parser.add_argument('-jt', '--job_type', action='store', default=' ',
                        help='Job Title')

    parser.add_argument('-n', '--number_of_jobs', action='store', type=int,
                        help="Amount of jobs to scrap")

    parser.add_argument('-rt', '--rating_threshold', action='store', type=int,
                        help="Get jobs info above certain overall rating threshold")

    parser.add_argument('-p', '--path', action='store', type=str, required=True,
                        help="File path to save the results in")

    parser.add_argument('-v', '--verbose', action='store_true',
                        help="Optional - Choose either printing output to std or not")

    # args = parser.parse_args()
    args = parser.parse_args(['-jt', 'Data Analyst', '-n', '100', '-p', 'res.csv'])

    return args


def main():

    args = parse_args()

    sm = ScraperManager(path=args.path, job_title=args.job_type, job_location=args.location,
                        rating_filter=args.rating_threshold, number_of_jobs=args.number_of_jobs)

    while sm.page_num <= sm.number_of_pages:

        # Find all jobs listing at the *current* page
        jobs = sm.find_num_of_jobs_on_page()

        # Iterate over the jobs found in the page
        for job in jobs:

            job_obj = Job(job, sm.driver)
            if job_obj.id >= sm.num_of_jobs:
                break
            print(f"Scraping job number {job_obj.id} out of {sm.num_of_jobs}", end='')
            job_obj.click()
            job_obj.get_common_params()

            try:
                sm.click_tab('company')
            except NoSuchElementException:
                pass
            finally:
                job_obj.get_non_common_params()

            sm.fill_dict(job_obj)

            try:
                sm.click_tab('rating')
            except NoSuchElementException:
                sm.update_nans()
            else:
                job_obj.get_ratings_scores()
                sm.update_jobs_data(job_obj.ratings)

            print('--Done')

        sm.click_tab('next')
        sm.page_num += 1

    sm.create_dataframe()
    sm.save_results()
    print('Done')


if __name__ == "__main__":
    main()
