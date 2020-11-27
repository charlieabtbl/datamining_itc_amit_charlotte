import mysql.connector

# Creating a list of tables
tables = []
job_ratings = '''CREATE TABLE Ratings(idRatings INT NOT NULL AUTO_INCREMENT PRIMARY KEY, Culture_values float, 
Diversity_inclusion float, Work_life_bal float, Senior_mngt float,  Benefits float, Career_opportunities float, 
Overall_rating float)'''
tables.append(job_ratings)
company = '''CREATE TABLE Company(idCompany INT NOT NULL AUTO_INCREMENT PRIMARY KEY, Company_name VARCHAR(25) NOT 
NULL, Size_est VARCHAR(25), Revenue_est VARCHAR(25), Industry VARCHAR(25), idRatings INT, FOREIGN KEY(idRatings) 
REFERENCES Ratings(idRatings))'''
tables.append(company)
job_post = '''CREATE TABLE Job_post(idJob_post INT NOT NULL AUTO_INCREMENT PRIMARY KEY, Title VARCHAR(25) NOT NULL, 
Salary_range VARCHAR(30), idCompany INT, FOREIGN KEY (idCompany) REFERENCES Company(
idCompany))'''
tables.append(job_post)
job_location = '''CREATE TABLE Job_location(idJob_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY, City VARCHAR(25), 
State VARCHAR(10))'''
tables.append(job_location)
job_post_location = '''CREATE TABLE Job_post_location(idJob_post_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY,  
idJob_post INT, idJob_location INT, FOREIGN KEY (idJob_post) REFERENCES Job_post(idJob_post), FOREIGN KEY (
idJob_location) REFERENCES Job_location(idJob_location))'''
tables.append(job_post_location)
# Building the database

def create_database(host_name, user_name, password):
    '''Define the connection and the cursor that is used for executing the SQL commands and
    creates the database glassdoor'''

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


def create_tables(host_name, user_name, password, db_name, tables):
    my_db = mysql.connector.connect(host=host_name, user=user_name, passwd=password, database= db_name)
    cursor = my_db.cursor()
    # Execute all SQL commands and commit them into the DB
    for table in tables:
        cursor.execute(table)
    my_db.commit()

    # Close database connection
    cursor.close()
    my_db.close()

def main():
    create_database('localhost', 'root', 'Cabtbl-20')
    create_tables('localhost', 'root', 'Cabtbl-20', 'glassdoor_db', tables)


if __name__ == "__main__":
    main()
