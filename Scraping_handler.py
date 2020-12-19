from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from selenium import webdriver
from bs4 import BeautifulSoup
import random
import time
import re

BASE_URL = "https://www.glassdoor.com/Job/palo-alto-data-scientist-jobs-SRCH_IL.0,9_IC1147434_KO10,24.htm"
COMPANY_TAG = {"data-tab-type": "overview"}
RATING_TAG = {"data-tab-type": "rating"}
COMPANY_ERRORS = []
RATING_ERRORS = []


def insert_search_criteria(driver, job_type, location):

    driver.find_element_by_xpath('.//input[@name="sc.keyword"]').clear()
    driver.find_element_by_xpath('.//input[@name="sc.keyword"]'). \
        send_keys(job_type)

    time.sleep(random.uniform(1, 1.5))

    driver.find_element_by_xpath('.//input[@id="sc.location"]').clear()
    driver.find_element_by_xpath('.//input[@id="sc.location"]'). \
        send_keys(location)

    time.sleep(random.uniform(1, 1.5))

    driver.find_element_by_xpath('.//button[@id="HeroSearchButton"]').click()


def bypass_login(driver):
    try:
        driver.find_element_by_class_name("selected").click()
    except ElementClickInterceptedException:
        pass

    try:
        driver.find_element_by_class_name("modal_closeIcon").click()
    except NoSuchElementException:
        pass


def get_num_of_matched_jobs(driver):

    page_content = BeautifulSoup(driver.page_source, "html.parser")
    raw = page_content.find('div', attrs={"data-test": "jobCount-H1title"})

    if raw:
        match = re.search(r"(^\d+)", raw.text)
        return int(match.group())
    else:
        driver.close()
        raise ValueError("Your search criteria yield no results\n"
                      "Consider changing your search")


def get_common_data(bs_job):

    data = dict()
    data['Company_Name'] = bs_job.find("div", class_="jobHeader").text
    data["Job_Title"] = bs_job.find('a', attrs={"class": "jobTitle"}).text
    city, state = get_job_location(bs_job)
    data["City"] = city
    data['State'] = state
    min_salary, max_salary = get_job_salary(bs_job)
    data['Min_Salary'] = min_salary
    data['Max_Salary'] = max_salary

    return data


def get_job_location(bs_job):
    raw_location = bs_job.find('span', attrs={"class": "loc"})
    if raw_location:
        location = raw_location.text.split(',')
        city = location[0]
        state = location[1] if len(location) > 1 else None
    else:
        return None, None

    return city, state


def get_job_salary(bs_job):
    raw_salary = bs_job.find('span', attrs={"class": "css-18034rf"})
    if raw_salary:
        salary_estim = raw_salary.text
        salary_range = re.findall("\$(\d+\w*)\S+\$(\d+\w*)", salary_estim)
        min_sal = salary_range[0][0]
        max_sal = salary_range[0][1]
    else:
        return None, None

    return min_sal, max_sal


def get_company_data(driver):

    page_content = BeautifulSoup(driver.page_source, "html.parser")

    if page_content.find('div', COMPANY_TAG):

        xpath = './/div[@class="tab" and @data-tab-type="overview"]'
        wait = WebDriverWait(driver, 3)
        button = wait.until(EC.presence_of_element_located((By.XPATH,
                                                            xpath)))

        driver.execute_script("arguments[0].click();", button)
        driver.execute_script("arguments[0].click();", button)

        time.sleep(2)

        page_content = BeautifulSoup(driver.page_source, "html.parser")
        tab_content = page_content.find("div", attrs={"id": "EmpBasicInfo"})

        retries = 3
        while tab_content is None:
            if retries == 0:
                COMPANY_ERRORS.append(1)
                return {}
            tab_content = page_content.find("div", attrs={"id": "EmpBasicInfo"})
            retries -= 1

        entities = tab_content.find_all("div", attrs={"class": "infoEntity"})

        job_company = {}

        for ent in entities:
            field = ent.find('label').text
            value = ent.find('span').text
            job_company.update({field: value})

    else:
        return {}

    return job_company


def get_rating_data(driver, bs_job):

    page_content = BeautifulSoup(driver.page_source, "html.parser")

    if page_content.find('div', RATING_TAG):

        xpath = './/div[@class="tab" and @data-tab-type="rating"]'
        wait = WebDriverWait(driver, 3)
        button = wait.until(EC.presence_of_element_located((By.XPATH,
                                                            xpath)))

        driver.execute_script("arguments[0].click();", button)
        driver.execute_script("arguments[0].click();", button)

        time.sleep(2)

        overall_rating = bs_job.find("span", class_="compactStars").text
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        tab_content = page_content.find("ul", attrs={"class": "ratings"})

        retries = 3
        while tab_content is None:
            if retries == 0:
                RATING_ERRORS.append(1)
                return {}
            tab_content = page_content.find("ul", attrs={"class": "ratings"})
            retries -= 1

        entities = tab_content.find_all("li")

        job_ratings = {"Overall": overall_rating}

        for ent in entities:
            field = ent.find("span", attrs={"class": "ratingType"}).text
            value = ent.find("span", attrs={"class": "ratingNum"}).text
            job_ratings.update({field: value})
    else:
        return {}

    return job_ratings


def initiate_driver(chromedriver_path, args):
    USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.77 " \
                 "Safari/537.36 "

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    if args.headless:
        options.add_argument('--headless')
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-extensions')
        options.add_argument('--profile-directory=Default')
        options.add_argument("--incognito")
        options.add_argument("--disable-plugins-discovery")
        options.add_argument("--start-maximized")
        options.add_argument(f'--user-agent={USER_AGENT}')
    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(executable_path=chromedriver_path,
                              options=options)

    driver.get(BASE_URL)
    time.sleep(random.uniform(1, 1.5))
    bypass_login(driver)
    time.sleep(random.uniform(1, 2))
    insert_search_criteria(driver, args.job_type, args.location)

    return driver