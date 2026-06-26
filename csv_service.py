import csv
import os


def read_csv(file_path):
    if not os.path.exists(file_path):
        return []

    with open(file_path, mode="r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def write_csv(file_path, fieldnames, rows):
    with open(file_path, mode="w", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def append_csv(file_path, fieldnames, row):
    file_exists = os.path.exists(file_path)

    with open(file_path, mode="a", encoding="utf-8-sig", newline="") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)

        if not file_exists or os.path.getsize(file_path) == 0:
            writer.writeheader()

        writer.writerow(row)
