import mysql.connector

# Creating a list of tables
tables = []
job_ratings = '''CREATE TABLE Ratings(idRatings INT NOT NULL AUTO_INCREMENT PRIMARY KEY, Culture_values FLOAT, 
Diversity_inclusion FLOAT, Work_life_bal FLOAT, Senior_mngt FLOAT,  Benefits FLOAT, Career_opportunities FLOAT, 
Overall_rating FLOAT)'''
tables.append(job_ratings)
company = '''CREATE TABLE Company(idCompany INT NOT NULL AUTO_INCREMENT PRIMARY KEY, Company_name TEXT NOT 
NULL, Size_est TEXT, Revenue_est TEXT, Industry TEXT, idRatings INT, FOREIGN KEY(idRatings) 
REFERENCES Ratings(idRatings))'''
tables.append(company)
job_post = '''CREATE TABLE Job_post(idJob_post INT NOT NULL AUTO_INCREMENT PRIMARY KEY, Title TEXT NOT NULL, 
Salary_range TEXT, idCompany INT, FOREIGN KEY (idCompany) REFERENCES Company(
idCompany))'''
tables.append(job_post)
job_location = '''CREATE TABLE Job_location(idJob_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY, City VARCHAR(60), 
State VARCHAR(10))'''
tables.append(job_location)
job_post_location = '''CREATE TABLE Job_post_location(idJob_post_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY,  
idJob_post INT, idJob_location INT, FOREIGN KEY (idJob_post) REFERENCES Job_post(idJob_post), FOREIGN KEY (
idJob_location) REFERENCES Job_location(idJob_location))'''
tables.append(job_post_location)


# Building the database

def create_database(host_name, user_name, password):
    '''Take host_name, user_name and password as parameters to connect to mysql and returns a database with tables
    if it doesn't already exists '''

    # Connecting to the database
    my_db = mysql.connector.connect(host=host_name, user=user_name, passwd=password)
    cursor = my_db.cursor()

    # Making sure the database 'glassdoor' doesn't exist
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    if ('glassdoor_db',) not in databases:
        cursor.execute("CREATE DATABASE glassdoor_db")
        print('glassdoor_db was created')
    else:
        print('glassdoor_db already exists')
    cursor.close()
    my_db.close()


def create_tables(host_name, user_name, password, tables):
    # Connecting to the database
    my_db = mysql.connector.connect(host=host_name, user=user_name, passwd=password)
    cursor = my_db.cursor()

    # Making sure the database 'glassdoor' doesn't exist
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()
    if ('glassdoor_db',) not in databases:
        cursor.execute("CREATE DATABASE glassdoor_db")
        print('glassdoor_db was created')
        my_db = mysql.connector.connect(host=host_name, user=user_name, passwd=password, database='glassdoor_db')
        cursor = my_db.cursor()
        # Execute all SQL commands and commit them into the DB
        for table in tables:
            cursor.execute(table)
        my_db.commit()
    else:
        print('glassdoor_db already exists')
    cursor.close()
    my_db.close()




def main():
    create_tables('localhost', 'root', 'Cabtbl-20', tables)


if __name__ == "__main__":
    main()
