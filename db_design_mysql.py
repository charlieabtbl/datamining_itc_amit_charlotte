import mysql.connector

# Constants
DB_NAME = 'glassdoor'

# Creating a list of tables
tables = []

job_description = '''CREATE TABLE Job_description (
                            idJob_description int AUTO_INCREMENT, 
                            Description TEXT,
                            PRIMARY KEY(idJob_description);'''
tables.append(job_description)
job_ratings = ''''CREATE TABLE Ratings (
                            idRatings int AUTO_INCREMENT, 
                            Culture_values float,
                            Diversity_inclusion float,
                            Work_life_bal float,
                            Senior_mngt float,
                            Benefits float,
                            Career_opportunities float,
                            Overall_rating float,
                            PRIMARY KEY(idRatings) );'''
tables.append(job_ratings)

company= '''CREATE TABLE Company (
                            idCompany int AUTO_INCREMENT, 
                            Company_name TEXT NOT NULL,
                            Size_est TEXT,
                            Revenue_est TEXT,
                            Industry TEXT,
                            idRatings int,
                            PRIMARY KEY(idCompany),
                            FOREIGN KEY(idRatings) REFERENCES Ratings(idRatings));'''
tables.append(company)
job_post = '''CREATE TABLE Job_post (
                            idJob_post int AUTO_INCREMENT, 
                            Title TEXT NOT NULL,
                            Salary_range TEXT,
                            idJob_description INT,
                            idCompany INT,
                            PRIMARY KEY(idJob_post)
                            FOREIGN KEY (idJob_description) REFERENCES Job_description(idJob_description),
                            FOREIGN KEY (idCompany) REFERENCES Company(idCompany));'''
tables.append(job_post)

job_location = '''CREATE TABLE Job_location (
                            idJob_location int AUTO_INCREMENT, 
                            City TEXT,
                            State TEXT,
                            PRIMARY KEY(idJob_location));'''
tables.append(job_location)

job_post_location = '''CREATE TABLE Job_post_location (
                            idJob_post_location int AUTO_INCREMENT, 
                            idJob_post INT,
                            idJob_location INT,
                            PRIMARY KEY(idJob_post_location),
                            FOREIGN KEY (idJob_post) REFERENCES Job_post(idJob_post),
                            FOREIGN KEY (idJob_location) REFERENCES Job_location(idJob_location));'''
tables.append(job_post_location)


# Building the database
def create_database(host_name, user_name, password):
    mydb = mysql.connector.connect(
        host_name="localhost",
        user_name="root",
        password="Cabtbl-20"
    )
    mycursor = mydb.cursor()

    mycursor.execute("CREATE DATABASE glassdoor")


def build_database(db_name, host_name, user_name, password, tables):
    '''Define the connection and the cursor that is used for executing the SQL commands'''

    my_db = mysql.connector.connect(host=host_name, user=user_name, passwd=password, database=db_name)
    cursor = my_db.cursor()

    # Execute all SQL commands and commit them into the DB
    for table in tables:
        cursor.execute(table)
    my_db.commit()

    # Close database connection
    if my_db is not None and my_db.is_connected():
          cursor.close() ; my_db.close()

def main():
    ''' AMIT - Should we create a parser also for this ..?'''
    build_database(DB_NAME, 'localhost', 'root', 'Cabtbl-20', tables)


if __name__ == "__main__":
    main()
