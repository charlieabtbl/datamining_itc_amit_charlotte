from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.by import By
from pyvirtualdisplay import Display
from selenium import webdriver
from bs4 import BeautifulSoup
from tqdm import tqdm
import pathlib
import logging
import random
import time
import re

logger = logging.getLogger(__name__)

BASE_URL = "https://www.glassdoor.com/Job/palo-alto-data-scientist-jobs-SRCH_IL.0,9_IC1147434_KO10,24.htm"
COMPANY_TAG = {"data-tab-type": "overview"}
RATING_TAG = {"data-tab-type": "rating"}
COMPANY_ERRORS = []
RATING_ERRORS = []


def insert_search_criteria(driver, job_type, location):
    """
    Establishes website interaction for inserting the user's search parameters
    Being used as part of the driver initialization
    """
    logger.info(f"Inserting search parameters: Job Type: {job_type}, Location: {location}")
    driver.find_element_by_xpath('.//input[@name="sc.keyword"]').clear()
    driver.find_element_by_xpath('.//input[@name="sc.keyword"]').send_keys(job_type)

    time.sleep(random.uniform(1, 1.5))

    driver.find_element_by_xpath('.//input[@id="sc.location"]').clear()
    driver.find_element_by_xpath('.//input[@id="sc.location"]').send_keys(location)

    time.sleep(random.uniform(1, 1.5))

    driver.find_element_by_xpath('.//button[@id="HeroSearchButton"]').click()

    logger.info("Successfully inserted search parameters")


def bypass_login(driver):
    """
    Surpass the sign-up pop up by interacting with the web
    """

    try:
        driver.find_element_by_class_name("selected").click()
    except ElementClickInterceptedException:
        pass

    try:
        driver.find_element_by_class_name("modal_closeIcon").click()
    except NoSuchElementException:
        pass


def get_num_of_matched_jobs(driver):
    """
    Find the total amount of jobs presence, according to the user's search criteria
    Being used at do_scraping() function
    """
    logger.info("Extracting total number of jobs")
    page_content = BeautifulSoup(driver.page_source, "html.parser")
    raw = page_content.find('div', attrs={"data-test": "jobCount-H1title"})

    if raw:
        match = re.search(r"(^\d+)", raw.text)
        logger.info(f"Found {int(match.group())} jobs in total")
        return int(match.group())
    else:
        driver.close()
        logger.error("===Something went wrong===")
        raise ValueError("Your search criteria yield no results\n"
                         "Consider changing your search")


def get_common_data(bs_job):
    """
    Scrap data from the mainCol jobs list (regardless of the job's tabs)
    """
    logger.info("Extracting job's common data")
    data = dict()
    data['Company_Name'] = bs_job.find("div", class_="jobHeader").text
    data["Job_Title"] = bs_job.find('a', attrs={"class": "jobTitle"}).text
    city, state = get_job_location(bs_job)
    data["City"] = city
    data['State'] = state
    min_salary, max_salary = get_job_salary(bs_job)
    data['Min_Salary'] = min_salary
    data['Max_Salary'] = max_salary
    logger.info(f"Job's data:\n\t{data}")

    return data


def get_job_location(bs_job):
    """
    Extract job's location using BeautifulSoup
    """
    logger.info("Extracting job's location")
    raw_location = bs_job.find('span', attrs={"class": "loc"})
    if raw_location:
        location = raw_location.text.split(',')
        city = location[0]
        state = location[1] if len(location) > 1 else None
    else:
        return None, None

    return city, state


def get_job_salary(bs_job):
    """
    Extracting job's salary using BeautifulSoup
    """
    logger.info("Extracting job's salary")
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
    """
    This function interacts with the web, clicking this specific job's company tab (if present)
    and extract pre-defined data.
    """
    logger.info("Extracting job's company tab data")
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
                logger.error("For some reason, could not scrap the tab content")
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
        logger.info("Has no 'Company' tab")
        return {}

    logger.info(f"Job's company tab data:\n\t{job_company}")
    return job_company


def get_rating_data(driver, bs_job):
    """
    This function interacts with the web, clicking this specific job's rating tab (if present)
    and extract pre-defined data.
    """
    logger.info("Extracting job's rating tab data")
    page_content = BeautifulSoup(driver.page_source, "html.parser")

    if page_content.find('div', RATING_TAG):

        xpath = './/div[@class="tab" and @data-tab-type="rating"]'
        wait = WebDriverWait(driver, 3)
        button = wait.until(EC.presence_of_element_located((By.XPATH,
                                                            xpath)))

        driver.execute_script("arguments[0].click();", button)
        driver.execute_script("arguments[0].click();", button)

        time.sleep(random.uniform(1, 3))

        try:
            overall_rating = bs_job.find("span", class_="compactStars").text
        except AttributeError as e:
            logger.error(f"===Could not get Overall Rating: {e}===")
            return {}
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        tab_content = page_content.find("ul", attrs={"class": "ratings"})

        retries = 3
        while tab_content is None:
            if retries == 0:
                RATING_ERRORS.append(1)
                logger.error("For some reason, could not scrap the tab content")
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
        logger.info("Has no Rating tab")
        return {}

    logger.info(f"Job's Rating tab data:\n\t{job_ratings}")
    return job_ratings


def initiate_driver(chromedriver_path, platform, args):
    """
    Initiating Chromedriver instance for interacting with the website
    """
    logger.info("Initiating Chrome Driver")
    if platform.lower() == 'linux':
        display = Display(visible=0, size=(800, 800))
        display.start()

    options = webdriver.ChromeOptions()
    options.add_argument('--ignore-certificate-errors')
    options.add_argument('--incognito')
    if args.headless:
        options.add_argument('--headless')

    options.add_experimental_option('excludeSwitches', ['enable-logging'])

    driver = webdriver.Chrome(executable_path=chromedriver_path,
                              options=options)

    driver.get(BASE_URL)
    time.sleep(random.uniform(1, 1.5))
    bypass_login(driver)
    time.sleep(random.uniform(1, 2))
    insert_search_criteria(driver, args.job_type, args.location)

    logger.info("Chrome Driver has been initiated successfully")

    return driver


def get_chromedriver_path(configurations):

    # Get Driver Path
    logger.info("Deriving Google Chrome driver file")
    driver_path = pathlib.Path.cwd().joinpath(configurations['Scraping']['chromedriver'])
    if isinstance(driver_path, pathlib.WindowsPath):
        if len(driver_path.as_posix().split('.')) > 1:
            if driver_path.as_posix().split('.')[1] == 'exe':
                driver_path = driver_path.as_posix()
            else:
                logger.error("Could not locate properly Google Chrome driver")
                raise IOError("Check your chromedriver file suffix in the configuration file")
        else:
            driver_path = driver_path.with_suffix(".exe").as_posix()
    else:
        driver_path = driver_path.as_posix()

    logger.info("Found Google Chrome driver!")

    return driver_path


def do_scraping(args, configurations):
    """
    The main function of this module.
    This function called by the main() function in the Gg_scrap.py script file
    """
    general_data = []
    company_tab_data = []
    ratings_tab_data = []

    try:
        driver_path = get_chromedriver_path(configurations)
    except IOError as e:
        logger.error(e)
        raise IOError(e)

    platform = configurations['Scraping']['Platform']
    driver = initiate_driver(driver_path, platform, args)

    try:
        jobs_found = get_num_of_matched_jobs(driver)
    except ValueError as e:
        logger.error(e)
        raise ValueError(e)

    jobs_to_scrap = min(args.number_of_jobs, jobs_found) if args.number_of_jobs else jobs_found
    job_id = 1
    pbar = tqdm(total=jobs_to_scrap, desc="Scraping progress", ncols=100)
    while len(general_data) < jobs_to_scrap:
        logger.debug("Inside the While loop")
        # Jobs on specific page
        jobs_list = driver.find_elements_by_class_name("jl")
        page_content = BeautifulSoup(driver.page_source, "html.parser")
        bs_jobs_list = page_content.find_all("li", class_="jl")
        for idx, job in enumerate(jobs_list, start=1):
            logger.debug("Inside the For loop")
            if len(general_data) == jobs_to_scrap:
                break

            logger.info(f"Job Number: {job_id}")
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
                pbar.update(1)

        # Click 'Next' Button
        logger.info("Moving to next page")
        xpath = './/a[@data-test="pagination-next"]'
        wait = WebDriverWait(driver, 3)
        next_button = wait.until(EC.presence_of_element_located((By.XPATH, xpath)))
        next_button.click()
        time.sleep(random.uniform(1, 2))

    driver.close()

    return general_data, company_tab_data, ratings_tab_data