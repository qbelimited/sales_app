from app import app, db
from models.help_model import HelpStep
from sqlalchemy.exc import IntegrityError

# Define the help steps as a list of dictionaries for easy management
help_steps_data = [
    {
        "page_name": "sales-targets",
        "target": "h1.text-center",
        "content": "Welcome to the Sales Targets Management page. Here you can view, add, edit, and delete sales targets.",
        "order": 1
    },
    {
        "page_name": "sales-targets",
        "target": 'Button[variant="primary"]',
        "content": "Click here to add a new sales target. Fill in the details in the modal that appears.",
        "order": 2
    },
    {
        "page_name": "sales-targets",
        "target": 'select[name="sales_manager_id"]',
        "content": "Use these dropdowns to filter sales targets by manager and criteria type. This helps you focus on specific targets.",
        "order": 3
    },
    {
        "page_name": "sales-targets",
        "target": 'input[type="date"]',
        "content": "Select a date range to filter the sales targets within specific periods.",
        "order": 4
    },
    {
        "page_name": "sales-targets",
        "target": "Table",
        "content": "This table displays your sales targets. You can see the sales manager, target count, premium amount, criteria types, and periods.",
        "order": 5
    },
    {
        "page_name": "sales-targets",
        "target": 'Button[variant="warning"]',
        "content": "For each target, you have options to edit or delete. Use these buttons to manage your sales targets effectively.",
        "order": 6
    },
    {
        "page_name": "sales-targets",
        "target": 'Button[variant="secondary"]',
        "content": "Click this button to toggle the view of past sales targets that are no longer active.",
        "order": 7
    },
    {
        "page_name": "sales-targets",
        "target": "Pagination",
        "content": "Use these pagination controls to navigate through multiple pages of sales targets.",
        "order": 8
    },
    {
        "page_name": "sales",
        "target": "h2.text-left",
        "content": "Welcome to the Sales Records page. Here you can manage your sales records, filter, and sort them easily.",
        "order": 1
    },
    {
        "page_name": "sales",
        "target": 'Button[variant="primary"]',
        "content": "Click here to add a new sale record. Fill in the details in the modal that appears.",
        "order": 2
    },
    {
        "page_name": "sales",
        "target": 'Button[variant="info"], Button[variant="warning"], Button[variant="danger"], Button[variant="secondary"]',
        "content": "Use these buttons to filter sales records by their status: Submitted, Under Investigation, or Rejected. Reset filters to show all records.",
        "order": 3
    },
    {
        "page_name": "sales",
        "target": 'DatePicker',
        "content": "Select a date range to filter sales records created within specific periods.",
        "order": 4
    },
    {
        "page_name": "sales",
        "target": 'input[name="clientName"]',
        "content": "Use this field to filter records by name. Start typing to find a match.",
        "order": 5
    },
    {
        "page_name": "sales",
        "target": "Table",
        "content": "This table displays all sales records. You can see details such as Client Name, Amount, Policy Type, and Status.",
        "order": 6
    },
    {
        "page_name": "sales",
        "target": 'Button[variant="primary"]',
        "content": "Click here to view detailed information about the sale record.",
        "order": 7
    },
    {
        "page_name": "manage-users-sessions",
        "target": "h1.text-center.mb-4",
        "content": "Welcome to the Manage User Sessions page. Here, you can view and manage all active user sessions.",
        "order": 1
    },
    {
        "page_name": "manage-users-sessions",
        "target": 'SessionTable',
        "content": "This table displays all active user sessions. You can see details such as user information and session status.",
        "order": 2
    },
    {
        "page_name": "manage-users-sessions",
        "target": 'Button',
        "content": "Click this button to end a user's session. This action will log the user out from their current session.",
        "order": 3
    },
    {
        "page_name": "manage-users",
        "target": "h1.text-center.mb-4",
        "content": "Welcome to the Manage Users page. Here you can view and manage the list of users in the system.",
        "order": 1
    },
    {
        "page_name": "manage-users",
        "target": 'TableWithPagination',
        "content": "This table displays all registered users. You can view details such as name, email, role, and the date they were created.",
        "order": 2
    },
    {
        "page_name": "manage-sales-executives",
        "target": "h1.text-center.mb-4",
        "content": "Welcome to the Sales Executive Management page. Here you can view, add, edit, and delete sales executives.",
        "order": 1
    },
    {
        "page_name": "manage-sales-executives",
        "target": 'Button[variant="contained"]',
        "content": "Click this button to add a new sales executive. A form will pop up for you to fill in their details.",
        "order": 2
    },
    {
        "page_name": "manage-sales-executives",
        "target": 'Table',
        "content": "This table displays all sales executives, showing their name, code, phone number, and assigned manager.",
        "order": 3
    },
    {
        "page_name": "manage-sales-executives",
        "target": 'Action Buttons',
        "content": "Use these buttons to view details, edit, or delete a sales executive's information.",
        "order": 4
    },
    {
        "page_name": "manage-roles",
        "target": "h2",
        "content": "Welcome to the Manage Roles page. Here you can create, edit, and delete roles for users.",
        "order": 1
    },
    {
        "page_name": "manage-roles",
        "target": 'Table',
        "content": "This table displays all existing roles. You can view their names, descriptions, and take actions on them.",
        "order": 2
    },
    {
        "page_name": "manage-products",
        "target": "h4",
        "content": "Welcome to the Product Management page. Here you can manage your products, including creating, editing, and deleting them.",
        "order": 1
    },
    {
        "page_name": "manage-products",
        "target": 'Table',
        "content": "This table displays all existing products. You can view their names, categories, groups, and take actions on them.",
        "order": 2
    },
    {
        "page_name": "manage-paypoints",
        "target": "h4",
        "content": "Welcome to the Paypoint Management page. Here you can manage all your paypoints, including adding, editing, and deleting them.",
        "order": 1
    },
    {
        "page_name": "manage-paypoints",
        "target": 'Button',
        "content": "Click this button to add a new paypoint. A form will pop up for you to enter the paypoint details.",
        "order": 2
    },
    {
        "page_name": "manage-paypoints",
        "target": 'Table',
        "content": "This table displays all existing paypoints. You can view their names and locations, and take action on them.",
        "order": 3
    },
    {
        "page_name": "manage-branches",
        "target": "h4",
        "content": "Welcome to the Branch Management page. Here you can manage all your branches, including adding, editing, and deleting them.",
        "order": 1
    },
    {
        "page_name": "manage-branches",
        "target": 'Button',
        "content": "Click this button to add a new branch. A form will pop up for you to enter the branch details.",
        "order": 2
    },
    {
        "page_name": "manage-branches",
        "target": 'Table',
        "content": "This table displays all existing branches. You can view their names, addresses, Ghana Post GPS, city, and region.",
        "order": 3
    },
    {
        "page_name": "manage-banks",
        "target": "h4",
        "content": "Welcome to the Bank and Branch Management page. Here you can manage banks and their branches, including adding, editing, and deleting them.",
        "order": 1
    },
    {
        "page_name": "manage-banks",
        "target": 'Button',
        "content": "Click this button to add a new bank. A form will pop up for you to enter the bank's details.",
        "order": 2
    },
    {
        "page_name": "manage-banks",
        "target": 'Table',
        "content": "This table displays all existing banks. You can view their names and perform actions such as editing or deleting.",
        "order": 3
    },
    {
        "page_name": "investigations",
        "target": "h2",
        "content": "Welcome to the Under Investigation Records page. Here you can manage records that are under investigation, including viewing, editing, and resolving them.",
        "order": 1
    },
    {
        "page_name": "investigations",
        "target": 'Button',
        "content": "Click this button to run an auto-update on all investigation records. This action will refresh the data.",
        "order": 2
    },
    {
        "page_name": "investigations",
        "target": 'Alert',
        "content": "This section explains the meaning of critical and potential duplicates in the records.",
        "order": 3
    },
    {
        "page_name": "investigations",
        "target": 'Table',
        "content": "This table displays all records under investigation. You can view the details, reasons, notes, and actions available for each record.",
        "order": 4
    },
    {
        "page_name": "dashboard",
        "target": '.navbar',
        "content": "This is the navigation bar where you can find the log out button and the profile button to update your password. Ensure to update your password from the default password.",
        "order": 1
    },
    {
        "page_name": "dashboard",
        "target": '.sidebar',
        "content": "Here is the sidebar with different modules of the app; use it to navigate the application.",
        "order": 2
    },
]

with app.app_context():
    for step_data in help_steps_data:
        # Check if the help step already exists
        existing_step = db.session.query(HelpStep).filter_by(
            page_name=step_data['page_name'],
            target=step_data['target'],
            order=step_data['order']
        ).first()

        if not existing_step:
            help_step = HelpStep(
                page_name=step_data['page_name'],
                target=step_data['target'],
                content=step_data['content'],
                order=step_data['order']
            )
            db.session.add(help_step)

    try:
        db.session.commit()
        print("Help steps seeded successfully!")
    except IntegrityError:
        db.session.rollback()
        print("Error while seeding help steps. Please check for duplicates or constraints.")
