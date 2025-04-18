import csv
from difflib import get_close_matches

# Sales Manager targets from the provided information
targets_info = {
    '180': [
        'Edmund Nketia', 'Ransford Sarpong', 'Daniel Tanson', 'Seth Ofori Amankwah', 'Deborah Johnson',
        'John Dzeble', 'Emmanuel Tsifokor', 'Hayford Osae', 'Emmanuel Tandoh', 'Emmanuel Asankomah',
        'Prince Antwi Mensah', 'Isaac Takyi', 'Emmanuel Obeng-Mensah'
    ],
    '165': ['Antoinette Safo'],
    '150': [
        'Lawson Atidigah', 'Daniel Gyamfi', 'Emmanuel Dickson Gyamfi', 'Daniel Anel Ankrah',
        'Nathaniel Akugri', 'Nana Nkuah Nkrumah', 'Sumaila Abdul - Razak', 'PETERCLARK ABADAMKIA'
    ]
}

# Convert a string to sentence case (capitalize first letter of each word)
def to_sentence_case(name):
    return ' '.join(word.capitalize() for word in name.split())

# Read the users.csv and filter only Sales Managers, storing their original case
def read_users_csv(users_csv_file):
    sales_managers = []

    with open(users_csv_file, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)

        # Collect only users who are Sales Managers
        for row in csv_reader:
            if row['Role'].strip() == 'Sales_Manager':
                name = row['Name'].strip()
                email = row['Email'].strip()
                sales_managers.append((name, email))  # (Original Name, Email) Tuple

    return sales_managers

# Split names into components (first, middle, last) for matching
def split_name(name):
    return name.split()

# Match names based on two or three components
def match_names(target_name, sales_managers):
    # Split the target name into components
    target_components = split_name(target_name)

    # Try to match with at least two or three components
    for name, email in sales_managers:
        user_components = split_name(to_sentence_case(name))  # Match against sentence case
        # Ensure matching at least 2 components (e.g., first and last name)
        matches = set(target_components).intersection(user_components)
        if len(matches) >= 2:
            return name  # Return the original case name from users.csv

    # If no match is found, return None
    return None

# Write matched names into a new CSV with their original spelling from users.csv
def write_matched_names_to_csv(matched_names, output_csv_file):
    with open(output_csv_file, mode='w', newline='', encoding='utf-8-sig') as csvfile:
        fieldnames = ['Target', 'Name']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()

        for target_group, names in matched_names.items():
            for name in names:
                writer.writerow({'Target': target_group, 'Name': name})

# Get sales managers from users.csv
users_csv_file = './users.csv'  # Path to the CSV file
sales_managers = read_users_csv(users_csv_file)

# Match all target names with the users from CSV
matched_names = {}
for target_group, target_names in targets_info.items():
    matched_names[target_group] = []

    for target_name in target_names:
        target_name_sentence_case = to_sentence_case(target_name)  # Convert target name to sentence case for matching
        matched_name = match_names(target_name_sentence_case, sales_managers)
        if matched_name:
            matched_names[target_group].append(matched_name)
        else:
            print(f"Could not match: {target_name}")

# Write matched names to a new CSV using their original names from users.csv
output_csv_file = './corrected_sales_managers.csv'  # Path for the output CSV
write_matched_names_to_csv(matched_names, output_csv_file)

print(f"Corrected names written to {output_csv_file}")
