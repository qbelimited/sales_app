import csv
from app import app, db
from models.user_model import Role, User
from models.bank_model import Bank, BankBranch
from models.branch_model import Branch
from models.impact_product_model import ImpactProduct
from models.paypoint_model import Paypoint
from models.sales_executive_model import SalesExecutive

# Replace 'your_csv_file.csv' with the path to your actual CSV file for banks
csv_file_path = './banks.csv'

with app.app_context():
    # Seed Roles
    admin_role = Role(name='admin', description='Administrator')
    sales_manager_role = Role(name='manager', description='Sales Manager')
    back_office_role = Role(name='back_office', description='Sales Officer back office')
    user_role = Role(name='user', description='Normal user')
    db.session.add(admin_role)
    db.session.add(user_role)
    db.session.add(back_office_role)
    db.session.add(sales_manager_role)
    db.session.commit()

    # Seed Banks and BankBranches
    unique_banks = {}
    with open(csv_file_path, newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            bank_name = row['BANK NAME'].strip()
            branch_name = row['BRANCH NAME'].strip()
            branch_code = row['SORT CODE'].strip()

            if bank_name not in unique_banks:
                bank = Bank(name=bank_name)
                db.session.add(bank)
                db.session.commit()  # Commit to get the bank ID
                unique_banks[bank_name] = bank.id
            else:
                bank_id = unique_banks[bank_name]

            # Create BankBranch entry
            branch = BankBranch(
                name=branch_name,
                bank_id=unique_banks[bank_name],
                sort_code=branch_code
            )
            db.session.add(branch)

    # Commit all unique bank and branch entries to the database
    db.session.commit()

    # Seed Impact Products
    products = [
        {'name': 'EDUCARE', 'category': 'Retail'},
        {'name': 'FAREWELL', 'category': 'Retail'},
        {'name': 'PENSION', 'category': 'Retail'}
    ]
    unique_products = set()

    for product_data in products:
        if product_data['name'] not in unique_products:
            unique_products.add(product_data['name'])
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
        'Atwima Kwanwoma Rurak Bank',
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
        'Ghana Water Co.-Ashanti production',
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
        'odotobri Rural Bank',
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
        'Akim Bosome Rural Rank',
        'Charles Wesley Foundation International School',
        'Ghana Bauxite Company Limited'
    ]

    unique_pay_points = set()

    for point in pay_points:
        if point not in unique_pay_points:
            unique_pay_points.add(point)
            pay_point = Paypoint(name=point)
            db.session.add(pay_point)

    db.session.commit()

    # Seed Branches (Used by Users and Sales Executives)
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

    unique_branches = {}
    for branch_name in branches:
        if branch_name not in unique_branches:
            branch = Branch(name=branch_name)
            db.session.add(branch)
            db.session.commit()  # Commit to get branch ID
            unique_branches[branch_name] = branch.id

    # Seed Sales Managers and Sales Executives
    # sales_data = [
    #     {'agent_code': 'R00013271', 'manager_name': 'DEBORAH JOHNSON', 'executive_name': 'EVANS ADU BOATENG', 'branch_name': 'ASYLUM DOWN'},
    #     {'agent_code': 'R00013269', 'manager_name': 'SETH OFORI AMANKWAH', 'executive_name': 'AARON AMIHERE', 'branch_name': 'ASYLUM DOWN'},
    #     {'agent_code': 'R00013890', 'manager_name': 'EMMANUEL OBENG-MENSAH', 'executive_name': 'AARON BAY MORKEH', 'branch_name': 'SUNYANI'},
    #     {'agent_code': 'R00013380', 'manager_name': 'LAWSON ATIDIGAH', 'executive_name': 'AARON DZANSI - BUATSI', 'branch_name': 'HOHOE'},
    #     {'agent_code': 'R00013462', 'manager_name': 'GODFRED NII ARYEE HAYFORD', 'executive_name': 'ABA KOOMSON', 'branch_name': 'TAKORADI'},
    #     {'agent_code': 'R00013744', 'manager_name': 'ABDUL AZIZ SALIFU', 'executive_name': 'ABDUL - RAZAK MULAIKA', 'branch_name': 'TAMALE'},
    #     {'agent_code': 'R00013742', 'manager_name': 'ABDUL AZIZ SALIFU', 'executive_name': 'ABDUL - WADUD ALHASSAN', 'branch_name': 'TAMALE'},
    #     {'agent_code': 'R00013730', 'manager_name': 'ABDUL AZIZ SALIFU', 'executive_name': 'ABDUL - WAHID DRAMUNDU SALIFU', 'branch_name': 'TAMALE'},
    #     {'agent_code': 'R00013305', 'manager_name': 'RANSFORD DANIEL SARPONG', 'executive_name': 'ABDUL KADIR MAJID DWOMOH', 'branch_name': 'ASYLUM DOWN'},
    #     {'agent_code': 'R00013433', 'manager_name': 'ABDUL AZIZ SALIFU', 'executive_name': 'ABDULAI ABDUL- RAHMAN', 'branch_name': 'TAMALE'},
    #     {'agent_code': 'R00013915', 'manager_name': 'SUMAILA ABDUL - RAZAK', 'executive_name': 'ABDUL-RAUF ISSAHAKU', 'branch_name': 'TAMALE'},
    #     {'agent_code': 'R00013797', 'manager_name': 'RANSFORD DANIEL SARPONG', 'executive_name': 'ABENA ASABERE AFRIYIE', 'branch_name': 'ASYLUM DOWN'},
    #     {'agent_code': 'R00013496', 'manager_name': 'HAYFORD OSAE', 'executive_name': 'ABIGAIL ABA FOWA AMOO', 'branch_name': 'KASOA'},
    # ]

    # unique_sales_managers = {}

    # for data in sales_data:
    #     # Handle the Sales Manager
    #     if data['manager_name'] not in unique_sales_managers:
    #         sales_manager = User(
    #             email=f"{data['manager_name'].replace(' ', '.').lower()}@example.com",  # Generate a unique email
    #             name=data['manager_name'],
    #             role_id=sales_manager_role.id,
    #             is_active=True
    #         )
    #         db.session.add(sales_manager)
    #         db.session.commit()
    #         unique_sales_managers[data['manager_name']] = sales_manager.id
    #     else:
    #         sales_manager_id = unique_sales_managers[data['manager_name']]

    #     # Handle the Sales Executive
    #     sales_executive = SalesExecutive(
    #         name=data['executive_name'],
    #         code=data['agent_code'],
    #         manager_id=unique_sales_managers[data['manager_name']],
    #     )

    #     # Associate the executive with the branch
    #     branch_id = unique_branches[data['branch_name']]
    #     sales_executive.branches.append(db.session.get(Branch, branch_id))

    #     db.session.add(sales_executive)

    db.session.commit()

    # Seed Admin User
    admin_user = User(email='admin@example.com', name='Admin User', role_id=admin_role.id, is_active=True)
    db.session.add(admin_user)
    db.session.commit()

    print("Database seeded successfully!")
