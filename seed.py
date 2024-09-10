import csv
from app import app, db
from models.bank_model import Bank, BankBranch
from models.branch_model import Branch
from models.impact_product_model import ImpactProduct, ProductCategory
from models.paypoint_model import Paypoint
from models.user_model import Role, User
from models.sales_executive_model import SalesExecutive
from werkzeug.security import generate_password_hash

# CSV file paths
sales_exec_csv_file = './sales_exec.csv'
csv_file_path = './banks.csv'
users_csv_file = './users.csv'

with app.app_context():
    # Seed Banks and BankBranches
    unique_banks = {}
    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            bank_name = row.get('BANK NAME', '').strip()
            branch_name = row.get('BRANCH NAME', '').strip()
            branch_code = row.get('SORT CODE', '').strip()

            existing_bank = db.session.query(Bank).filter_by(name=bank_name).first()
            if not existing_bank:
                bank = Bank(name=bank_name)
                db.session.add(bank)
                db.session.commit()
                unique_banks[bank_name] = bank.id
            else:
                unique_banks[bank_name] = existing_bank.id

            existing_branch = db.session.query(BankBranch).filter_by(name=branch_name, bank_id=unique_banks.get(bank_name)).first()
            if not existing_branch:
                branch = BankBranch(
                    name=branch_name,
                    bank_id=unique_banks.get(bank_name),
                    sort_code=branch_code
                )
                db.session.add(branch)

    db.session.commit()
    print("Banks and branches seeded successfully!")

    # Seed Impact Product Categories
    categories = ['Retail', 'Corporate', 'Micro']
    category_dict = {}

    for category_name in categories:
        category = db.session.query(ProductCategory).filter_by(name=category_name).first()
        if not category:
            category = ProductCategory(name=category_name)
            db.session.add(category)
            db.session.commit()
        category_dict[category_name] = category.id

    # Seed Impact Products
    products = [
        {'name': 'EDUCARE', 'category': 'Retail', 'group': 'risk'},
        {'name': 'FAREWELL', 'category': 'Retail', 'group': 'risk'},
        {'name': 'PENSION', 'category': 'Retail', 'group': 'risk'}
    ]

    for product_data in products:
        product = db.session.query(ImpactProduct).filter_by(name=product_data['name'], category_id=category_dict[product_data['category']]).first()
        if not product:
            product = ImpactProduct(
                name=product_data['name'],
                category_id=category_dict[product_data['category']],
                group=product_data['group']
            )
            db.session.add(product)

    db.session.commit()
    print("Products seeded successfully!")

    # Seed Pay Points
    pay_points = [
        'Accra City Hotel',
        'Afram Community Bank - Maame Krobo',
        'Afram Community Bank - Nkawkaw',
        'Amansie Rural Bank',
        'Amenfiman Rural Bank',
        'Atwima Kwanwoma Rural Bank',
        'CAGD - GUA Life',
        'CAGD - Phoenix',
        'CHED',
        'Church of Pentecost-Konongo Area',
        'Cocoa Marketing Company',
        'COCOBOD',
        'Dannex Ayrton Drugs',
        'DDP Outdoor',
        'Dumpong Rural Bank-Asakraka',
        'Ga Rural Bank',
        'Ghana Armed Forces (MOD)',
        'Ghana Police Service',
        'Ghana Post Co. Ltd.',
        'Ghana Revenue Authority',
        'Ghana Water Co.-Accra East',
        'Ghana Water Co.-Accra East Production',
        'Ghana Water Co.-Accra West',
        'Ghana Water Co.-Ashanti Drilling',
        'Ghana Water Co.-Ashanti North',
        'Ghana Water Co.-Ashanti Production',
        'Ghana Water Co.-Ashanti South',
        'Ghana Water Co.-Bolgatanga',
        'Ghana Water Co.-Ho',
        'Ghana Water Co.-Koforidua',
        'Ghana Water Co.-Sunyani',
        'Ghana Water Co.-Takoradi',
        'Impact Life Insurance',
        'Kumawuman Rural Bank',
        'Multi Credit Savings and Loans',
        'MUMUADU RURAL BANK',
        'Nsoatreman Rural Bank',
        'Nwabiagya Rural Bank',
        'Odotobri Rural Bank',
        'Otuasekan Rural Bank',
        'Phoenix Ass. Co.-General',
        'Phyto-Riker Pharmaceuticals',
        'Quality Control Co. (Executives)',
        'Quality Control Co. (QCC)',
        'Seed Production',
        'South Akim Rural Bank',
        'PSG',
        'Dangbe Rural Bank',
        'Adonteng Rural Bank',
        'Kwahu Praso Rural Bank',
        'Akim Bosome Rural Bank',
        'Charles Wesley Foundation International School',
        'Ghana Bauxite Company Limited'
    ]

    for point in pay_points:
        pay_point = db.session.query(Paypoint).filter_by(name=point).first()
        if not pay_point:
            pay_point = Paypoint(name=point)
            db.session.add(pay_point)

    db.session.commit()
    print("Paypoints seeded successfully!")

    # Seed Branches
    branches = [
        'TAMALE',
        'TAKORADI',
        'ASYLUM DOWN',
        'KOFORIDUA',
        'KONONGO',
        'TEMA',
        'SUNYANI',
        'NKAWKAW',
        'SOGAKOPE',
        'HOHOE',
        'ASOKWA',
        'SWEDRU',
        'KASOA',
        'TECHIMAN',
        'OBUASI'
    ]

    for branch_name in branches:
        branch = db.session.query(Branch).filter_by(name=branch_name).first()
        if not branch:
            branch = Branch(name=branch_name)
            db.session.add(branch)

    db.session.commit()
    print("Branches seeded successfully!")

    # Seed Roles (Pre-existing roles for other parts of the app)
    roles_data = ['Back_office', 'Manager', 'Admin', 'Sales_Manager']
    roles_dict = {}

    for role_name in roles_data:
        role = db.session.query(Role).filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f'{role_name} role')
            db.session.add(role)
            db.session.commit()
        roles_dict[role_name] = role.id

    additional_roles = ['Super_admin']
    for role_name in additional_roles:
        role = db.session.query(Role).filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f'{role_name} role')
            db.session.add(role)
            db.session.commit()
        roles_dict[role_name] = role.id

    # Seed Users from CSV with Debugging
    with open(users_csv_file, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            name = row.get('Name', '').strip()
            email = row.get('Email', '').strip()
            phone_number = row.get('Phone number', '').strip()
            role_name = row.get('Role', '').strip()

            # Skip the record if the email is empty
            if not email:
                print(f"Skipping user {row.get('Name', 'Unknown')} due to missing email.")
                continue

            # Find or create the user
            user = db.session.query(User).filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    name=name,
                    password_hash=generate_password_hash('Password'),  # Set a default password
                    is_active=True,
                    is_deleted=False
                )
                # Assign the role to the user
                if role_name in roles_dict:
                    user.role_id = roles_dict[role_name]
                else:
                    print(f"Role '{role_name}' not found for user '{name}', skipping.")
                    continue

                db.session.add(user)

    db.session.commit()
    print("Users and roles seeded successfully!")

    # Define the Sales Manager role before using it
    sales_manager_role = db.session.query(Role).filter_by(name='Sales Manager').first()
    if not sales_manager_role:
        sales_manager_role = Role(name='Sales Manager', description='Sales Executive Manager')
        db.session.add(sales_manager_role)
        db.session.commit()

    # Seed Sales Executives from CSV file
    unique_sales_managers = {}

    with open(sales_exec_csv_file, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            agent_code = row.get('AGENTCODE', '').strip()
            manager_name = row.get('SALE MANAGER', '').strip()
            executive_name = row.get('SALES EXECUTIVE', '').strip()
            branch_name = row.get('BRANCH', '').strip()
            phone_number = row.get('TELEPHONE ', '').strip()

            if not agent_code:
                print(f"Skipping {executive_name} due to missing agent code.")
                continue

            # Ensure the manager exists as a user with flexible name checking
            if manager_name not in unique_sales_managers:
                # Split the manager name for a flexible pattern search (assumes first and last name)
                manager_name_parts = manager_name.split(' ')
                search_pattern = f"%{'%'.join(manager_name_parts)}%"

                # Perform a case-insensitive search using the SQL LIKE operator
                sales_manager = db.session.query(User).filter(
                    User.name.ilike(search_pattern)
                ).first()

                if not sales_manager:
                    print(f"Sales manager '{manager_name}' not found in the User table, skipping {executive_name}.")
                    continue  # Skip the sales executive if no matching manager is found

                # Cache the sales manager ID for later reuse
                unique_sales_managers[manager_name] = sales_manager.id

            # Handle missing or duplicate phone numbers
            if not phone_number:
                print(f"Skipping {executive_name} due to missing phone number.")
                continue

            # Check if a sales executive with the same phone number already exists
            existing_executive = db.session.query(SalesExecutive).filter_by(phone_number=phone_number).first()
            if existing_executive:
                print(f"Skipping {executive_name} due to duplicate phone number: {phone_number}")
                continue

            branch = db.session.query(Branch).filter_by(name=branch_name).first()
            if branch:
                sales_executive = db.session.query(SalesExecutive).filter_by(name=executive_name).first()
                if not sales_executive:
                    sales_executive = SalesExecutive(
                        name=executive_name,
                        code=agent_code,
                        phone_number=phone_number,
                        manager_id=unique_sales_managers[manager_name]
                    )
                    sales_executive.branches.append(branch)
                    db.session.add(sales_executive)
            else:
                print(f"Branch {branch_name} not found, skipping sales executive {executive_name}.")

    db.session.commit()
    print("Sales executives seeding completed successfully!")
    print("All Seeding completed successfully!")
