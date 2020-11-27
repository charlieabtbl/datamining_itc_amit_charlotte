import csv
import mysql.connector
import notebook

conn = mysql.connector.connect(host='localhost', user='root', passwd='Cabtbl-20', database='glassdoor')
cursor = conn.cursor()

with open('res.csv', 'r') as f:
    dict_reader = csv.DictReader(f)
    # Initializing primary keys
    idCompany = 0
    idRatings = 0
    idJob_post = 0
    idJob_description = 0
    idJob_post_location=0
    idJob_location = 0

    for j, row in notebook.tqdm(enumerate(dict_reader), total=X):
        cursor.execute('''INSERT INTO Ratings (idRatings, 
                            Culture_values,
                            Diversity_inclusion,
                            Work_life_bal,
                            Senior_mngt,
                            Benefits,
                            Career_opportunities,
                            Overall_rating) 
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)''',
                    [idRatings, row['Culture & Values'], row['Diversity & Inclusion'], row['Work/Life Balance'], row['Senior Management'],
                     row['Comp & Benefits'],row['Career Opportunities'],row['Overall Rating']])

        cursor.execute('''INSERT INTO Company (Company_name, Size_est, Revenue_est, Industry, idRatings) 
        VALUES (?, ?, ?, ?, ?)''',
        [idCompany, row['Company'], row['Company_Size'], row['Revenue'], row['Industry'], idRatings])

        cursor.execute('''INSERT INTO Job_post (idJob_post, Title, Salary_range, idJob_description, idCompany)
                        VALUES (?, ?, ?, ?, ?)''',
        [idJob_post, row['Title'], row['Salary'], idJob_description, idCompany])

        cursor.execute('''INSERT INTO Job_location (idJob_location int, City, State) 
        VALUES (?, ?, ?)''',
        [idJob_location, row[''], row['']])

        cursor.execute('''INSERT INTO Job_post_location (idJob_post_location int, idJob_post, idJob_location) 
        VALUES (?, ?, ?)''',
        [idJob_post_location, idJob_post, idJob_location])

        idCompany+=1
        idRatings += 1
        idJob_description+=1
        idJob_post+=1
        idJob_post_location +=1
        idJob_location+=1

        cursor.commit()

        cursor.close()




