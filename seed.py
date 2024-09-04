import csv
from app import app, db
from models.bank_model import Bank, BankBranch
from models.branch_model import Branch
from models.impact_product_model import ImpactProduct
from models.paypoint_model import Paypoint
from models.user_model import Role, User
from models.sales_executive_model import SalesExecutive

# CSV file path for Sales Executives
sales_exec_csv_file = './sales_executives.csv'

# Replace 'your_csv_file.csv' with the path to your actual CSV file for banks
csv_file_path = './banks.csv'

with app.app_context():
    unique_banks = {}
    with open(csv_file_path, newline='', encoding='utf-8-sig') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            bank_name = row.get('BANK NAME', '').strip()
            branch_name = row.get('BRANCH NAME', '').strip()
            branch_code = row.get('SORT CODE', '').strip()

            # Check if bank already exists in the database
            existing_bank = db.session.query(Bank).filter_by(name=bank_name).first()
            if not existing_bank:
                bank = Bank(name=bank_name)
                db.session.add(bank)
                db.session.commit()  # Commit to get the bank ID
                unique_banks[bank_name] = bank.id
            else:
                unique_banks[bank_name] = existing_bank.id

            # Create BankBranch entry
            branch = BankBranch(
                name=branch_name,
                bank_id=unique_banks.get(bank_name),
                sort_code=branch_code
            )
            db.session.add(branch)

    db.session.commit()

    # Seed Impact Products
    products = [
        {'name': 'EDUCARE', 'category': 'Retail'},
        {'name': 'FAREWELL', 'category': 'Retail'},
        {'name': 'PENSION', 'category': 'Retail'}
    ]
    for product_data in products:
        product = db.session.query(ImpactProduct).filter_by(name=product_data['name']).first()
        if not product:
            product = ImpactProduct(name=product_data['name'], category=product_data['category'])
            db.session.add(product)

    db.session.commit()

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

    # Seed Roles
    roles_data = {
        'Super admin': ['ekbotchway@impactlife.com.gh', 'hdogli@impactlife.com.gh', 'ryeboah@impactlife.com.gh'],
        'Back_office': ['enartey@impactlife.com.gh'],
        'Manager': ['fappau@impactlife.com.gh']
    }

    for role_name, emails in roles_data.items():
        role = db.session.query(Role).filter_by(name=role_name).first()
        if not role:
            role = Role(name=role_name, description=f'{role_name} role')
            db.session.add(role)
            db.session.commit()

        for email in emails:
            user = db.session.query(User).filter_by(email=email).first()
            if not user:
                user = User(email=email, name=email.split('@')[0], role_id=role.id, is_active=True)
                db.session.add(user)

    db.session.commit()

    # Define the sales_manager_role here before using it
    sales_manager_role = db.session.query(Role).filter_by(name='Sales manager').first()
    if not sales_manager_role:
        sales_manager_role = Role(name='Sales manager', description='Sales Executive Manager')
        db.session.add(sales_manager_role)
        db.session.commit()

    # Seed Sales Executives from CSV file
    unique_sales_managers = {}

    with open(sales_exec_csv_file, newline='', encoding='utf-8') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            agent_code = row.get('AGENTCODE', '').strip()
            manager_name = row.get('SALE MANAGER', '').strip()
            executive_name = row.get('SALES EXECUTIVE', '').strip()
            branch_name = row.get('BRANCH', '').strip()
            phone_number = row.get('TELEPHONE', '').strip()

            # Handle the Sales Manager
            if manager_name not in unique_sales_managers:
                sales_manager = User(
                    email=f"{manager_name.replace(' ', '.').lower()}@example.com",
                    name=manager_name,
                    role_id=sales_manager_role.id,
                    is_active=True
                )
                db.session.add(sales_manager)
                db.session.commit()
                unique_sales_managers[manager_name] = sales_manager.id

            # Handle the Sales Executive
            branch = db.session.query(Branch).filter_by(name=branch_name).first()
            if branch:
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

    print("Roles, users, and sales executives seeded successfully!")
