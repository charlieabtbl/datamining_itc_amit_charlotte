from Stocks_API import *
import mysql.connector
import logging
import json
import csv

logger = logging.getLogger('glassdoor_scraping.log')


def connect(func):
    def inner(*args, **kwargs):
        host, username, password, db_name = _parse_json('config.json')

        logger.info("Establishing mySQL connection")
        db_connection = mysql.connector.connect(host=host, user=username, passwd=password)
        mysql_cursor = db_connection.cursor()
        logger.info("Connection established successfully")
        mysql_cursor.execute(f"USE {db_name}")

        func(db_connection, mysql_cursor, db_name, *args, **kwargs)

        db_connection.commit()
        mysql_cursor.close()
        db_connection.close()
        logger.info("mySQL connection closed")

    return inner


@connect
def create_database(my_db, cursor, db_name, *args, **kwargs):
    """
    Create new mySQL database (if not exists yet)
    """

    logger.info(f"Creating Database: {db_name}")
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {db_name}")
    my_db.commit()
    cursor.execute("SHOW DATABASES")
    databases = cursor.fetchall()

    # Sanity check
    if (db_name.lower(),) in databases:
        logger.info(f"Successfully created {db_name} Database")
    else:
        logger.error("Could not create Database")


def create_scarping_tables():
    """
    Construct mySQL commands for creating the tables in the database
    """
    logger.info("Constructing mySQL commands for creating tables")
    crate_table_commands = {}

    job_ratings = '''CREATE TABLE IF NOT EXISTS Ratings(idRatings INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                          Culture_values FLOAT, 
                                          Diversity_inclusion FLOAT,
                                          Work_life_balance FLOAT,
                                          Senior_management FLOAT, 
                                          Benefits FLOAT,
                                          Career_opportunities FLOAT, 
                                          Overall_rating FLOAT)'''

    crate_table_commands["Ratings"] = job_ratings

    company = '''
    CREATE TABLE IF NOT EXISTS Company(idCompany INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                         Company_name VARCHAR(45) NOT NULL, 
                         Min_Size INT,
                         Max_Size INT, 
                         Revenue_est TEXT, 
                         Industry VARCHAR(50), 
                         idRatings INT, 
                         FOREIGN KEY(idRatings) REFERENCES Ratings(idRatings))'''

    crate_table_commands["Company"] = company

    job_post = '''
    CREATE TABLE IF NOT EXISTS Job_post(idJob_post INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                          Title TEXT NOT NULL, 
                          Min_Salary VARCHAR(10),
                          Max_Salary VARCHAR(10), 
                          idCompany INT, 
                          FOREIGN KEY (idCompany) REFERENCES Company(idCompany))'''

    crate_table_commands["Job_post"] = job_post

    job_location = '''
    CREATE TABLE IF NOT EXISTS Job_location(idJob_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY, 
                              City VARCHAR(45), 
                              State VARCHAR(10))'''

    crate_table_commands["Job_location"] = job_location

    job_post_location = '''
    CREATE TABLE IF NOT EXISTS Job_post_location(idJob_post_location INT NOT NULL AUTO_INCREMENT PRIMARY KEY,  
                                   idJob_post INT,
                                   idJob_location INT,
                                   FOREIGN KEY (idJob_post) REFERENCES Job_post(idJob_post),
                                   FOREIGN KEY (idJob_location) REFERENCES Job_location(idJob_location))'''

    crate_table_commands["Job_post_location"] = job_post_location

    logger.info("Done constructing tables commands")

    for table_name, sql_query in crate_table_commands.items():
        create_table(table_name, sql_query)


def create_api_table():
    """
    This function creates specific table fot storing scraped data from a free public API
    """
    sql_query = '''CREATE TABLE IF NOT EXISTS 
                   Company_stock_details(idCompany_stock_details INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                         idCompany INT,  
                                         Stock_price FLOAT, 
                                         Market_cap FLOAT,
                                         Currency VARCHAR(10), 
                                         Website TEXT,
                                         Ex_Market VARCHAR(10),
                                         FOREIGN KEY(idCompany) REFERENCES Company(idCompany))'''

    create_table('Company_stock_details', sql_query)


@connect
def create_table(my_db, cursor, db_name, table_name, query, *args, **kwargs):
    """
    Execute mySQL query for creating table in a given data base
    :param my_db - mySQL database connection
    :param cursor - mySQL connection cursor
    :param db_name - str - The database name you'd like to work on
    :param table_name - str - The table name you'd like to create
    :param query - mySQL query (str) to execute
    """
    logger.info(f"Creating {table_name} table")
    cursor.execute(query)
    my_db.commit()
    logger.info(f"{table_name} created successfully")


@connect
def show_query(my_db, cursor, db_name, show_what, table_name=None):
    """
    Assistant function to construct and execute 'mySQL' SHOW commands
    """
    if show_what.lower() == 'databases':
        sql_query = "SHOW DATABASES"
    elif show_what.lower() == 'tables':
        sql_query = f"SHOW TABLES IN {db_name}"
    elif show_what.lower() == 'columns':
        sql_query = f"SHOW COLUMNS IN {table_name}"

    else:
        raise IOError("show_what argument must be either 'databases' or 'tables'")

    cursor.execute(sql_query)
    res = cursor.fetchall()
    return res


@connect
def insert_values(my_db, cursor, db_name, where_from='file'):
    """
    Insert values into given mySQL table.
    :param my_db - mySQL database connection
    :param cursor - mySQL connection cursor
    :param db_name - str - The database name you'd like to work on
    :param where_from - str - Whether insert values from a CSV file ('file') from an API output ('api')
    """
    with open('config.json') as config_file:
        config_params = json.load(config_file)

    data_file = config_params['Scraping']['results_path']

    # Extracting relevant data from the csv file
    if where_from.lower() == 'file':

        with open(fr"{data_file}", 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)

            for line_num, line in enumerate(reader):
                line = replace_nans(line)
                ratings_data = line[11:]

                cursor.execute('''INSERT INTO Ratings (Culture_values, 
                                                       Diversity_inclusion,
                                                       Work_life_balance,  
                                                       Senior_management,
                                                       Benefits,
                                                       Career_opportunities,
                                                       Overall_rating)
                                 VALUES (%s, %s, %s, %s, %s, %s, %s )''', ratings_data)

                idRatings = cursor.lastrowid

                cursor.execute('''INSERT INTO Company (Company_name,
                                                       Min_Size, 
                                                       Max_Size, 
                                                       Revenue_est, 
                                                       Industry, 
                                                       idRatings
                                                       ) 
                                  VALUES (%s, %s, %s, %s, %s, %s)''',
                               (line[1], line[7], line[8], line[9], line[10], idRatings))

                idCompany = cursor.lastrowid

                cursor.execute('''INSERT INTO Job_post (Title, 
                                                        Min_Salary, 
                                                        Max_Salary, 
                                                        idCompany)
                                  VALUES (%s, %s, %s, %s)''', (line[4], line[5], line[6], idCompany))

                idJob_post = cursor.lastrowid

                cursor.execute('''INSERT INTO Job_location (City, State) 
                                  VALUES (%s, %s)''', (line[2], line[3]))

                idJob_location = cursor.lastrowid

                cursor.execute('''INSERT INTO Job_post_location (idJob_post, idJob_location) 
                                  VALUES (%s, %s)''', (idJob_post, idJob_location))

                if line_num % 50 == 0:
                    logger.info("Committing changes")
                    my_db.commit()
                    logger.info("Done committing changes")

    elif where_from.lower() == 'api':
        sql_query = "SELECT idCompany, Company_name from company"
        cursor.execute(sql_query)
        companies = cursor.fetchall()
        for idx, company in companies:

            stock_price, market_cap, currency, website, exchange_market = extract_info_API(company[0])
            sql_query = """INSERT INTO Company_stock_details (Stock_price,
                                                              Market_cap,
                                                              Currency ,
                                                              Website,
                                                              Ex_Market,
                                                              idCompany)
                          VALUES (%s, %s, %s, %s, %s, %s)"""

            cursor.execute(sql_query, (stock_price, market_cap, currency, website, exchange_market, idx))

            if idx % 50 == 0:
                my_db.commit()


def replace_nans(val_list):
    """
    Replace missing values with nans.
    Making it easier for the mySQL to handle with.
    An auxiliary function to insert_values()
    """
    fixed_list = [item if item != '' else None for item in val_list]

    return fixed_list


def _parse_json(json_file):
    """
    Internal function for parsing JSON configuration file
    This function extracts database parameters out of given JSON file
    """
    with open(json_file, 'r') as config_file:
        db_params = json.load(config_file)['Database']

    host = db_params['host']
    user = db_params['username']
    password = db_params['password']
    db_name = db_params['database_name']

    return host, user, password, db_name


if __name__ == "__main__":
    create_database()
