#!/usr/bin/env python3
import csv
import os

csv_file = os.path.expanduser('~/compass_kansas_results/publication_analysis/tables/kansas_ALL_years_amr_phage_colocation.csv')

with open(csv_file) as f:
    reader = csv.DictReader(f)
    # Get first row
    first_row = next(reader)
    print("CSV Column Names:")
    print("=" * 50)
    for col in first_row.keys():
        print(f"  - {col}")
    print("\n" + "=" * 50)
    print("\nFirst row sample:")
    for key, value in first_row.items():
        print(f"  {key}: {value}")
