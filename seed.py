import csv
from app import app, db
from models.bank_model import Bank, BankBranch
from models.branch_model import Branch
from models.impact_product_model import ImpactProduct, ProductCategory
from models.performance_model import SalesTarget
from models.paypoint_model import Paypoint
from models.user_model import Role, User
from models.retention_model import RetentionPolicy
from models.access_model import Access
from models.sales_executive_model import SalesExecutive
from datetime import datetime
from sqlalchemy.exc import IntegrityError
import calendar
from werkzeug.security import generate_password_hash

# CSV file paths
sales_exec_csv_file = './sales_exec.csv'
csv_file_path = './banks.csv'
users_csv_file = './users.csv'
targets_csv_file = './targets.csv'

# Helper function to calculate the number of days in the current month
def get_days_in_current_month():
    year = datetime.utcnow().year
    month = datetime.utcnow().month
    return calendar.monthrange(year, month)[1]

# Monthly targets based on the provided breakdown (use integers as keys)
monthly_targets = {
    180: 180,
    165: 165,
    150: 150
}

# Define daily target and premium amount calculations
daily_target_sales_count = 10
daily_target_premium_amount = 1000

with app.app_context():
    # Seed Banks and BankBranches
    unique_banks = {}
    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            bank_name = row.get('BANK NAME', '').strip()
            branch_name = row.get('BRANCH NAME', '').strip()
            branch_code = row.get('SORT CODE', '').strip()

            # Check if the bank already exists
            existing_bank = db.session.query(Bank).filter_by(name=bank_name).first()
            if not existing_bank:
                bank = Bank(name=bank_name)
                db.session.add(bank)
                db.session.commit()
                unique_banks[bank_name] = bank.id
            else:
                unique_banks[bank_name] = existing_bank.id

            # Check if the branch already exists under the bank
            existing_branch = db.session.query(BankBranch).filter_by(name=branch_name, bank_id=unique_banks[bank_name]).first()
            if not existing_branch:
                branch = BankBranch(name=branch_name, bank_id=unique_banks[bank_name], sort_code=branch_code)
                db.session.add(branch)

    db.session.commit()  # Commit after adding all branches
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
        {'name': 'EDUCARE', 'category': 'Retail', 'group': 'investment'},
        {'name': 'FAREWELL', 'category': 'Retail', 'group': 'risk'},
        {'name': 'PENSION', 'category': 'Retail', 'group': 'investment'},
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

    db.session.commit()  # Commit after adding all products
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

            if not email:  # Skip the record if the email is empty
                print(f"Skipping user {row.get('Name', 'Unknown')} due to missing email.")
                continue

            user = db.session.query(User).filter_by(email=email).first()
            if not user:
                user = User(
                    email=email,
                    name=name,
                    password_hash=generate_password_hash('Password'),  # Set a default password
                    is_active=True,
                    is_deleted=False
                )
                if role_name in roles_dict:
                    user.role_id = roles_dict[role_name]
                else:
                    print(f"Role '{role_name}' not found for user '{name}', skipping.")
                    continue

                db.session.add(user)

    db.session.commit()  # Commit after adding all users
    print("Users and roles seeded successfully!")

    # Seed Access Rules for each role
    access_rules = [
        {
            'role_name': 'Back_office',
            'can_create': True,
            'can_update': True,
            'can_delete': False,
            'can_view_logs': False,
            'can_manage_users': False,
            'can_view_audit_trail': True
        },
        {
            'role_name': 'Manager',
            'can_create': True,
            'can_update': True,
            'can_delete': False,
            'can_view_logs': False,
            'can_manage_users': True,
            'can_view_audit_trail': True
        },
        {
            'role_name': 'Admin',
            'can_create': True,
            'can_update': True,
            'can_delete': True,
            'can_view_logs': True,
            'can_manage_users': True,
            'can_view_audit_trail': True
        },
        {
            'role_name': 'Sales_Manager',
            'can_create': True,
            'can_update': True,
            'can_delete': False,
            'can_view_logs': False,
            'can_manage_users': False,
            'can_view_audit_trail': False
        },
        {
            'role_name': 'Super_admin',
            'can_create': True,
            'can_update': True,
            'can_delete': True,
            'can_view_logs': True,
            'can_manage_users': True,
            'can_view_audit_trail': True
        }
    ]

    for rule in access_rules:
        role = db.session.query(Role).filter_by(name=rule['role_name']).first()

        if not role:
            print(f"Role '{rule['role_name']}' not found, skipping access rule seeding.")
            continue

        existing_access = db.session.query(Access).filter_by(role_id=role.id).first()
        if not existing_access:
            access_rule = Access(
                role_id=role.id,
                can_create=rule['can_create'],
                can_update=rule['can_update'],
                can_delete=rule['can_delete'],
                can_view_logs=rule['can_view_logs'],
                can_manage_users=rule['can_manage_users'],
                can_view_audit_trail=rule['can_view_audit_trail']
            )
            db.session.add(access_rule)

    db.session.commit()
    print("Access rules seeded successfully!")

    # Seed Retention Policy with 1-year retention period
    retention_policy = db.session.query(RetentionPolicy).first()
    if not retention_policy:
        retention_policy = RetentionPolicy(retention_days=365)
        db.session.add(retention_policy)
        db.session.commit()
        print("Retention policy seeded successfully with a 1-year period.")
    else:
        print("Retention policy already exists.")

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
                manager_name_parts = manager_name.split(' ')
                search_pattern = f"%{'%'.join(manager_name_parts)}%"
                sales_manager = db.session.query(User).filter(User.name.ilike(search_pattern)).first()

                if not sales_manager:
                    print(f"Sales manager '{manager_name}' not found, skipping {executive_name}.")
                    continue

                unique_sales_managers[manager_name] = sales_manager.id

            if not phone_number:
                print(f"Skipping {executive_name} due to missing phone number.")
                continue

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

    # Seed Targets
    # Open the CSV file containing Sales Manager names and their corresponding targets
    with open(targets_csv_file, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            # Get the monthly target and sales manager name
            monthly_target_type = int(row.get('Target', '').strip())
            sales_manager_name = row.get('Name', '').strip()

            # Convert the integer target into the corresponding string key
            monthly_target_key = f"{monthly_target_type}_cases"

            # Validate the target type
            if monthly_target_type not in monthly_targets:
                print(f"Invalid target type for Sales Manager {sales_manager_name}, skipping...")
                continue

            # Fetch the Sales Manager from the database based on the name
            sales_manager = db.session.query(User).filter(User.name.ilike(f'%{sales_manager_name}%')).first()
            if not sales_manager:
                print(f"Sales Manager {sales_manager_name} not found, skipping...")
                continue

            # Set the monthly target sales count and premium amount
            monthly_target_sales_count = monthly_targets[monthly_target_type]
            monthly_target_premium_amount = monthly_target_sales_count * 100  # Premium target per case is 100 GHC

            # Calculate the number of days in the current month
            days_in_month = get_days_in_current_month()

            # Calculate daily targets
            daily_target_sales_count = monthly_target_sales_count / days_in_month
            daily_target_premium_amount = monthly_target_premium_amount / days_in_month

            # Calculate the fraction of targets for paypoints and risk group
            paypoint_target_sales_count = monthly_target_sales_count * 0.80  # 80% of the monthly target
            risk_group_target_sales_count = monthly_target_sales_count * 0.70  # 70% of the monthly target

            # Set the Paypoint Target as a SalesTarget entry (for the month)
            paypoint_target = SalesTarget(
                sales_manager_id=sales_manager.id,
                target_sales_count=paypoint_target_sales_count,  # 80% of the total sales count
                target_premium_amount=paypoint_target_sales_count * 100,  # Corresponding premium amount
                target_criteria_type='source_type',  # Dynamic criteria type
                target_criteria_value='paypoint',  # Dynamic criteria value
                period_start=datetime(datetime.utcnow().year, datetime.utcnow().month, 1),  # Start of the current month
                period_end=datetime(datetime.utcnow().year, datetime.utcnow().month, days_in_month)  # End of the current month
            )
            db.session.add(paypoint_target)

            # Set the Risk Product Group Target as a SalesTarget entry (for the month)
            risk_group_target = SalesTarget(
                sales_manager_id=sales_manager.id,
                target_sales_count=risk_group_target_sales_count,  # 70% of the total sales count
                target_premium_amount=risk_group_target_sales_count * 100,  # Corresponding premium amount
                target_criteria_type='product_group',  # Dynamic criteria type
                target_criteria_value='risk',  # Dynamic criteria value (for risk products)
                period_start=datetime(datetime.utcnow().year, datetime.utcnow().month, 1),
                period_end=datetime(datetime.utcnow().year, datetime.utcnow().month, days_in_month)
            )
            db.session.add(risk_group_target)

            # Set the overall monthly target (including both risk and paypoint)
            monthly_target = SalesTarget(
                sales_manager_id=sales_manager.id,
                target_sales_count=monthly_target_sales_count,  # Total monthly sales count
                target_premium_amount=monthly_target_premium_amount,  # Total premium amount
                target_criteria_type='overall',  # General monthly target
                target_criteria_value='monthly_total',  # Just a placeholder for the overall target
                period_start=datetime(datetime.utcnow().year, datetime.utcnow().month, 1),
                period_end=datetime(datetime.utcnow().year, datetime.utcnow().month, days_in_month)
            )
            db.session.add(monthly_target)

            # Commit to the database
            try:
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                print(f"Failed to create sales targets for {sales_manager_name}, possible duplicate entry.")

        print("Sales Target seeding completed successfully!")

    # All done!
    print("All Seeding completed successfully!")
