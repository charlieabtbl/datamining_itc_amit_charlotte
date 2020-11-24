import sqlite3
import os
import random
import contextlib
from tqdm import notebook

DB = 'glassdoor.db'

if os.path.exists(DB):
    os.remove(DB)

with contextlib.closing(sqlite3.connect(DB)) as con:  # auto-closes
    with con:  # auto-commits
        cur = con.cursor()
        cur.execute('''CREATE TABLE Job_description (
                            idJob_description INTEGER PRIMARY KEY AUTOINCREMENT, 
                            Description TEXT);''')
        cur.execute('''CREATE TABLE Ratings (
                            idRatings INTEGER PRIMARY KEY AUTOINCREMENT, 
                            Culture_values REAL,
                            Work_life_bal REAL,
                            Diversity_inclusion REAL,
                            Senior_mngt REAL,
                            Benefits REAL,
                            Career_opportunities REAL,
                            Overall_rating REAL );''')
        cur.execute('''CREATE TABLE Company (
                            idCompany INTEGER PRIMARY KEY AUTOINCREMENT, 
                            Company_name TEXT NOT NULL,
                            Size_est TEXT,
                            Revenue_est TEXT,
                            Industry TEXT,
                            idRatings INT,
                            FOREIGN KEY(idRatings) REFERENCES Ratings(idRatings));''')
        cur.execute('''CREATE TABLE Job_post (
                            idJob_post INTEGER PRIMARY KEY AUTOINCREMENT, 
                            Title TEXT NOT NULL,
                            Salary_range TEXT,
                            idJob_description INT,
                            idCompany INT,
                            FOREIGN KEY (idJob_description) REFERENCES Job_description(idJob_description),
                            FOREIGN KEY (idCompany) REFERENCES Company(idCompany));''')
        cur.execute('''CREATE TABLE Job_location (
                            idJob_location INTEGER PRIMARY KEY AUTOINCREMENT, 
                            City TEXT,
                            State TEXT);''')
        cur.execute('''CREATE TABLE Job_post_location (
                            idJob_post_location INTEGER PRIMARY KEY AUTOINCREMENT, 
                            idJob_post INT,
                            idJob_location INT,
                            FOREIGN KEY (idJob_post) REFERENCES Job_post(idJob_post),
                            FOREIGN KEY (idJob_location) REFERENCES Job_location(idJob_location));''')

        con.commit()




