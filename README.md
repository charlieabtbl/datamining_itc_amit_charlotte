# Data Mining Project
Git project repository:
https://github.com/charlieabtbl/datamining_itc_amit_charlotte.git


## Choice of website
We decided to scrape the job search platform Glassdoor (www.glassdoor.com). 
Founded in 2007 in California, Glassdoor is a website where current and former employees anonymously review companies. 
Glassdoor also allows users to anonymously submit and view salaries as well as search and apply for jobs on its platform.

## Objective
Our objective is to be able to get a csv file describing the current job offers from different companies, according to selected filters (location and type of position). 
This type of file could be very useful in a job search. 

## Our method
To do so, we started by scraping the pages with a specific filter : the job position 'Data Scientist' in the location 'Palo Alto'.

The next step was to generalize the search so that the user could choose his own filter from the command line and to design a database.


## Structure of the project
(1) GlassdoorScraper.py: 
    In this file : 
      - we imported all the necessary modules : requests, bs4, os, time, re, numpy
      - we defined three classes
        the Scrapper Manager : allows us to download the page contents, get the elements, and save them in a pandas dataframe
        the Job class : allows us to specifically extract the features and the urls of each job position. The features that we chose for now are the following : company name, title, location, number of stars (company's grade), and the salary estimation.
        the DataBaseManager : allows us to create the database and insert the scraped data in it. 
      - we defined the command line argument  
      we defined the main function, which scraps the job offers for Data Scientists in Palo Alto using two class objects scrap and job_object
 
(2) res.csv
    This file is the output from our scraping after running DataScraper.py. It's a csv file. 
    
(3) glassdoor_robots.txt
    This file is the robots.txt file from Glassdoor that informs others on what they are allowed to scrap or not on the website. 

(4) requirements.txt
This file informs on all the installations required to allow the code to run.

(5) db_design_mysql.py
This file contains the code for the sql database creation : creation of the database 'glassdoor_db' and creation of the tables.

## How to perform the scrape and create the database 

(1) Clone the git repository on your local system

(2) Open GlassdoorScraper.py and run with -h parameter to get help

(3) Download Chrome driver : https://chromedriver.storage.googleapis.com/index.html?path=87.0.4280.20/
and make sure to place it within the same directory of the script file.

(4) Run the script Glassdoor Scraper with 4 required arguments : 

2 positional:
- res_path = the file path to save the results in
- driver_filename = file name of your chrome driver

2 optional required : 
- --db-username root : use your database user name
- --db-password DB_PASSWORD : use your database login password

(5) Personalize your search ! Let's say you want Data Scientists Jobs in Palo Alto and create a database 'Glassdoor_db'
Add optional arguments :
- -l "Palo Alto"
- -jt "Data Scientist"
- -rt 4
- -v : if you want to see the progress on screen
- --db-name "Glassdoor_db" : choose database name as you wish 


WARNING : DO NOT USE SINGLE QUOTES WHEN ENTERING ARGUMENTS.
ONLY USE DOUBLE QUOTES

(6) Now press enter 

(7) OUTPUT : a csv file should be saved as res_path as the output and you can access the database model under the name you chose or GlassdoorDB (default name) in Workbench or by connecting to mySql in the terminal.

## The database GlassdoorDB

![Screenshot](GlassdoorDB.png)


We created 5 tables in total (including one connection table): 

- Company : this table contains the information related to the company that posted a job offer : idCompany (Primary key), Company_name, Min_size (minimum number of employees of the company), Max_size (maximum number of employees of the company), Revenue_est, Industry, idRatings (Foreign key that connects the table to the Ratings table  : 1 to many - 1 company can have 1 rating max while 1 rating can correspond to multiple companies)

- Job_post : this table contains the information related to the job position offer posted by each company : idJob_post (Primary key), Title (job position), Min_salary (minimum salary), Max_salary (maximum salary), idCompany (Foreign key that connects the table to the Company table : 1 to many - 1 company can have multiple job posts, while 1 job_post can only have 1 company)

- Ratings : this table contains the information related to the different variables of ratings for a company : idRatings (Primary key), Culture_values, Diversity_inclusion, Work_life_balance, Senior_management, Benefits, Career_opportunities, Overall_ratings

- Job_location : this table contains the information related to the location corresponding to the job offer :idJob_location (Primary key), City, State. This table has a many to many relationship with the Job_post table. Therefore we created a Job_post_location table as a connection table. 


