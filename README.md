# Data Mining : Glassdoor Job Search Platform
Git project repository:
https://github.com/charlieabtbl/datamining_itc_amit_charlotte.git


## Website : www.glassdoor.com. 
Founded in 2007 in California, Glassdoor is a website where current and former employees anonymously review companies. 
Glassdoor also allows users to anonymously submit and view salaries as well as search and apply for jobs on its platform.

## Objective
The objective of the project is to build a database describing the current job offers from different companies, according to selected filters (location and type of position) according to the user search.
This type of database could be very useful in a job search. 

## Method
(1) scraping Glassdoor job offers based on user's parameters<br>
(2) inserting scraped data into a database<br>
(3) enriching the data with stock information on selected companies<br>

## Structure of the project
(1) GlassdoorScraper.py: <br>
- Importing all the necessary modules<br> 
- Defining CLI arguments<br>
- Using the Scraping_handler, Results_handler and Database modules.<br>
       
(2) Robots.txt file: glassdoor_robots.txt<br>
- This file lists the permissions one can have while scraping Glassdoor website. 

(3) Modules requirements file: requirements.txt<br>
- This file informs on all the installations required to allow the code to run.

(4) config.json
Holds constants regarding :
- Scraper : Chromedriver name and final results csv file path
- Database : Hostname, Username, Password and chosen Database name

(5) Stock_API.py 
- This file holds the function that extracts the data from the Stock API. You do not need a publisher id for this API.

(6) Database.py
- This file contains the code to connect, design and insert scraped and API values to the database.

## Run the script

**Step 1: Installation** 
- Use python3 <= 3.6 
- Make sure you have installed mysql.connector properly 
- Clone the repository with the given link above

**Step 2: Download Chrome Driver**
- Get chrome driver from: https://chromedriver.storage.googleapis.com/index.html?path=87.0.4280.20/
- Place it within the same directory of the script file (**`Important`**)

**Step 3: Modify config.json**
- file in accordance to your setup

**Step 4: Running The Script**
- Open your console and run the script from within its directory
- Inspect the parameters you can pass by running the script with the -h flag first.
- Run the script with whatever parameters you wish
    
    Running Examples:
    * python GlassdoorScraper.py -h
    * python GlassdoorScraper.py -l "Palo Alto" -jt "Data Scientist"
    * python GlassdoorScraper.py -l "New York" -jt "Python Developer" -n 150
    * python GlassdoorScraper.py -l "San Francisco" -jt "Data Analyst" -n 200 --api
    * python GlassdoorScraper.py -l "Tel Aviv" -jt "FPGA Engineer" -n 10 --headless
    
<div class="alert alert-danger"><b>WARNING:</b> DO NOT USE SINGLE QUOTES WHEN ENTERING ARGUMENTS.
ONLY USE DOUBLE QUOTES</div><br>

**Step 5 OUTPUT** 
- CSV file should be saved
- A new MySQL database should be created

## Database

![Screenshot](GlassdoorDB.png)


Overall, the database has 6 different relational tables (including one connection table)

- Company: Contains information related to the company that posted a job offer : idCompany (Primary key), Company_name, Min_size (minimum number of employees of the company), Max_size (maximum number of employees of the company), Revenue_est, Industry, idRatings (Foreign key that connects the table to the Ratings table  : 1 to many - 1 company can have 1 rating max while 1 rating can correspond to multiple companies)

- Job_post : Contains information related to the job position offer posted by each company : idJob_post (Primary key), Title (job position), Min_salary (minimum salary), Max_salary (maximum salary), idCompany (Foreign key that connects the table to the Company table : 1 to many - 1 company can have multiple job posts, while 1 job_post can only have 1 company)

- Ratings : Contains information related to the different variables of ratings for a company : idRatings (Primary key), Culture_values, Diversity_inclusion, Work_life_balance, Senior_management, Benefits, Career_opportunities, Overall_ratings

- Job_location : Contains the information related to the location corresponding to the job offer :idJob_location (Primary key), City, State. This table has a many to many relationship with the Job_post table. Therefore we created a Job_post_location table as a connection table.

- Company_stock_details: Contains information related for each company's stock details (if there is any) 


