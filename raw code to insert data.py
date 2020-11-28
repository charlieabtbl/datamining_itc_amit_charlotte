import mysql.connector
import pandas as pd
import numpy as np

# Preparing the dataframe
data = pd.read_csv ('res.csv')
df = pd.DataFrame(data, columns= ['Company','Location','Title','Salary','Company_Size','Revenue','Industry','Culture & Values','Diversity & Inclusion','Work/Life Balance','Senior Management','Comp & Benefits','Career Opportunities','Overall Rating'])
df = df.replace({np.nan: None})

for index, row in df.iterrows():
    my_db = mysql.connector.connect(host='localhost', user='root', passwd='Cabtbl-20', database='glassdoor_db')
    cursor = my_db.cursor()
    cursor.execute('''INSERT INTO Ratings (Culture_values, Diversity_inclusion, Work_life_bal,  
    Senior_mngt, Benefits, Career_opportunities, Overall_rating) VALUES(%s, %s, %s, %s, %s, %s, %s )''',
                   [row['Culture & Values'], row['Diversity & Inclusion'], row['Work/Life Balance'],
                    row['Senior Management'], row['Comp & Benefits'],row['Career Opportunities'],row['Overall '
                                                                                                     'Rating']])
    idRatings = cursor.lastrowid
    cursor.execute('''INSERT INTO Company (Company_name, Size_est, Revenue_est, Industry, idRatings) 
    VALUES (%s, %s, %s, %s, %s)''',
    [row['Company'], row['Company_Size'], row['Revenue'], row['Industry'], idRatings])

    idCompany = cursor.lastrowid

    cursor.execute('''INSERT INTO Job_post (Title, Salary_range, idCompany)
                    VALUES (%s, %s, %s)''',
    [row['Title'], row['Salary'], idCompany])

    idJob_post = cursor.lastrowid

    try:
        cursor.execute('''INSERT INTO Job_location (City, State) 
        VALUES (%s, %s)''',
        [(row['Location'].split(','))[0], (row['Location'].split(','))[1]])
    except IndexError:
        cursor.execute('''INSERT INTO Job_location (City, State) 
        VALUES (%s, %s)''',
        [(row['Location'].split(','))[0], 'NA'])

    idJob_location = cursor.lastrowid

    cursor.execute('''INSERT INTO Job_post_location (idJob_post, idJob_location) 
    VALUES (%s, %s)''',
    [idJob_post, idJob_location])


    my_db.commit()
    my_db.close()
    cursor.close()




