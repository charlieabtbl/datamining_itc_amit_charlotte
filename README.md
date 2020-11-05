# datamining_itc_amit_charlotte


## Choice of website
We decided to scrape the job search platform Glassdoor (www.glassdoor.com). 
Founded in 2007 in California, Glassdoor is a website where current and former employees anonymously review companies. 
Glassdoor also allows users to anonymously submit and view salaries as well as search and apply for jobs on its platform.

## Objective
Our objective is to be able to get a csv file describing the current job offers from different companies, according to selected filters (location and type of position). 
This type of file could be very useful in a job search. 

## Method
To do so, we started by scraping the pages with a specific filter : the job position 'Data Scientist' in the location 'Palo Alto'.

The next step would be to generalize the search so that the user could choose his own filter from the command line. 

## Structure of the project
(1) DataScraper.py: 
    In this file : 
      - we imported all the necessary modules : requests, bs4, os, time, re, numpy
      - we defined two classes
        the Scrapper class : allows us to download the page contents, get the elements, and save them in a pandas dataframe
        the Job class : allows us to specifically extract the features and the urls of each job position. The features that we chose for now are the following : company name, title, location, number of stars (company's grade), and the salary estimation. 
      - we defined the main function, which scraps the job offers for Data Scientists in Palo Alto using two class objects scrap and job_object
 
(2) Temp_res_scrapping.csv
    This file is the output from our scraping after running DataScraper.py. It's a csv file, that is temporary, since our code will be modified over the steps. 
    
(3) glassdoor_robots.txt
    This file is the robots.txt file from Glassdoor that informs others on what they are allowed to scrap or not on the website. 

(4) requirements.txt
This file informs on all the installations required to allow the code to run.

