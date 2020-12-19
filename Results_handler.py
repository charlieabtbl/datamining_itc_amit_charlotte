import pandas as pd
import csv
import os


def save_to_csv(file_path, data, exp_fieldnames):

    with open(file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=exp_fieldnames)
        writer.writeheader()
        writer.writerows(data)


def merge_csvs(filepath):

    files = ["common.csv", "comp.csv",  "ratings.csv"]
    combined_df = pd.concat([pd.read_csv(f, encoding="ISO-8859-1") for f in files], axis=1)
    combined_df.to_csv(filepath, encoding='utf-8')

    for file in files:
        os.remove(file)


def create_csv_res_file(company_tab_data, general_data, ratings_tab_data, file_name):

    save_to_csv('comp.csv', company_tab_data, ['Size', 'Founded', 'Type', 'Industry', 'Sector', 'Revenue'])

    save_to_csv('common.csv', general_data, ['Company_Name', 'Job_Title', 'City', 'State',
                                             'Min_Salary', 'Max_Salary'])

    save_to_csv('ratings.csv', ratings_tab_data, ['Overall', 'Culture & Values', 'Diversity & Inclusion',
                                                  'Work/Life Balance', 'Senior Management', 'Comp & Benefits',
                                                  'Career Opportunities'])

    if os.path.exists(file_name):
        os.remove(file_name)

    merge_csvs(file_name)

