import requests
from bs4 import BeautifulSoup
import pandas as pd
import os
import time
import re
import numpy as np


class Scrapper:

    def __init__(self, base_url, num_pages=1):

        self._base_url = base_url
        self._num_pages = int(num_pages)
        self._pages_urls = self.build_pages_result_list()
        self._headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 Safari/537.36'}
        self._data = {'Company': [],
                      'Rating': [],
                      'Job_Title': [],
                      'Location': [],
                      'Salary': [],
                      'Job_Description': [],
                      'URL': []}

    def build_pages_result_list(self) -> list:
        """
        Building a list of pages urls to scrap later on
        """
        pages_urls = []
        for page_number in range(1, self._num_pages + 1):
            page_url = self._base_url + str(page_number) + ".htm"
            pages_urls.append(page_url)

        return pages_urls

    @property
    def pages(self):
        return self._pages_urls

    @property
    def headers(self):
        return self._headers

    @property
    def data(self):
        return self._data

    def build_data_dict(self, **kwargs):
        """
        Fill the _data dictionary with values from each job that was scraped
        Used at the main() function
        """
        for key, val in kwargs.items():
            self._data[key].append(val)

    def request_page(self, url):
        """
        Sends an HTTP GET request to a specific URL
        Being used in main() as the very first step of scraping
        """
        self.page = requests.get(url, headers=self.headers)
        if self.page.status_code != 200:
            raise ValueError(f"Excpected to get 200\nInstead got: {self.page.status_code}")

    def get_elements(self, html_tag, html_class=None):
        """
        Acquire specified elements from the 'result' Soup object
        :param html_tag: str - HTML tag to search for
        :param html_class: (optional) str - Specifing the HTML tag's class
        """
        if html_class:
            self.elements = self.result.find_all(html_tag, class_=fr"{html_class}")
        else:
            self.elements = self.result.find_all(html_tag)

    def init(self, unique_tag_id: str):
        """
        Initializing BeautifulSoup object
        :param unique_tag_id: string - An HTML tag to search for
        """
        self.soup = BeautifulSoup(self.page.content, features='html.parser')
        self.result = self.soup.find(id=unique_tag_id)

    def build_dataframe(self):
        """
        Build pandas DataFrame out of the _data dictionary
        Being used as the last step of the scarping process
        """
        self.df = pd.DataFrame(self.data)

    def save_data(self, path: str):
        """
        Save results to an external CSV file
        :param path: str - Path of the new file to save to
        """
        if ".csv" not in os.path.splitext(path):
            path += ".csv"
        self.df.to_csv(path)


class Job:
    _count = 0

    def __init__(self, job_tag, host_url):
        Job._count += 1
        self.id = Job._count

        self.host_url = host_url
        self._job_tag = job_tag

        self.url = np.nan
        self.stars = np.nan
        self.comp_name = np.nan
        self.title = np.nan
        self.location = np.nan
        self.salary = np.nan

    def extract_features(self):
        """
        Extract pre-defined features out of the Job page content
        """
        # Each job entry has to have COMPANY NAME, TITLE and LOCATION
        self.comp_name = self._job_tag.find("a", class_="css-10l5u4p e1n63ojh0 jobLink").text
        self.title = self._job_tag.find("a", class_="jobInfoItem jobTitle css-13w0lq6 eigr9kq1 jobLink").text
        self.location = self._job_tag.find('span', class_="loc css-nq3w9f pr-xxsm").text

        # Extract the NUMBER_OF_STARS feature, if there is any:
        find_stars = self._job_tag.find('span', class_="compactStars")
        self.stars = find_stars.text if find_stars is not None else np.nan

        # Extract the SALARY feature, if there is any:
        job_salary_estim = self._job_tag.find("span", class_="css-18034rf e1wijj242")
        salary_range = re.findall(r"(\d+K)(-)\$(\d+K)", str(job_salary_estim))
        self.salary = "".join(salary_range[0]) if len(salary_range) else np.nan

    def extract_url(self):
        """
        Get the URL of the current Job
        """
        self.url = 'https://www.glassdoor.com' + self._job_tag.find('a')['href']


def main():
    """
    The scrapping begins here!
    Uses two separate objects: Scrapper and Job
    Scrapper contains some common parameters
    Job contains parameters related for a specific job item
    :return:
    """
    scrap = Scrapper("https://www.glassdoor.com/Job/palo-alto-data-scientist-jobs-SRCH_IL.0,9_IC1147434_KO10,24_IP", 30)
    for url in scrap.pages:
        print(f'Scrapping url: {url}')
        scrap.request_page(url)

        scrap.init('MainCol')
        scrap.get_elements('li', "jl react-job-listing gdGrid")

        for job_ele in scrap.elements:

            job_object = Job(job_ele, url)

            print(f"Extracting data of job number: {job_object.id}")

            job_object.extract_features()

            job_object.extract_url()

            scrap.build_data_dict(Company=job_object.comp_name, Rating=job_object.stars,
                                  Job_Title=job_object.title, Location=job_object.location,
                                  Salary=job_object.salary, Job_Description="Unavailable ATM", URL=job_object.url)

        time.sleep(0.5)

    scrap.build_dataframe()
    scrap.save_data("Temp_res_scrapping.csv")


if __name__ == "__main__":
    main()
