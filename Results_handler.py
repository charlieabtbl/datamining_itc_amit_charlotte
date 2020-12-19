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

