from app import app, db
from models.help_model import HelpStep, HelpStepCategory
from sqlalchemy.exc import IntegrityError

# Define the help steps as a list of dictionaries for easy management
help_steps_data = [
    {
        "page_name": "sales-targets",
        "target": "h1.text-center",
        "content": "Welcome to the Sales Targets Management page! This is where you'll manage all your sales targets. You can create new targets, view existing ones, and track their progress. Let's walk through the key features.",
        "order": 1,
        "category": HelpStepCategory.INTRODUCTION.value
    },
    {
        "page_name": "sales-targets",
        "target": 'Button[variant="primary"]',
        "content": "To create a new sales target, click this 'Add Target' button. You'll need to specify the sales manager, target amount, criteria type, and the period for the target. For example, you might set a target of 100 policies for Q1 2024.",
        "order": 2,
        "category": HelpStepCategory.FEATURE.value
    },
    {
        "page_name": "sales-targets",
        "target": 'select[name="sales_manager_id"]',
        "content": "Use these filters to find specific targets. You can filter by sales manager, criteria type, and date range. This helps you focus on relevant targets. For instance, you can view all targets for a specific manager in Q1.",
        "order": 3,
        "category": HelpStepCategory.NAVIGATION.value
    },
    {
        "page_name": "sales-targets",
        "target": 'input[type="date"]',
        "content": "Select a date range to view targets within specific periods. You can view targets for the current quarter, fiscal year, or any custom period. This helps in planning and tracking progress.",
        "order": 4,
        "category": HelpStepCategory.NAVIGATION.value
    },
    {
        "page_name": "sales-targets",
        "target": "Table",
        "content": "This table shows all your sales targets. Each row displays the sales manager, target count, premium amount, criteria types, and the target period. You can sort by any column by clicking the column header.",
        "order": 5,
        "category": HelpStepCategory.FEATURE.value
    },
    {
        "page_name": "sales-targets",
        "target": 'Button[variant="warning"]',
        "content": "For each target, you can edit or delete it using these action buttons. Editing allows you to update target details, while deletion removes the target permanently. Be careful with deletion as it cannot be undone.",
        "order": 6,
        "category": HelpStepCategory.FEATURE.value
    },
    {
        "page_name": "sales-targets",
        "target": 'Button[variant="secondary"]',
        "content": "This toggle button lets you switch between active and past targets. Past targets are those that have expired or been completed. This helps you maintain a clean view of current targets.",
        "order": 7,
        "category": HelpStepCategory.NAVIGATION.value
    },
    {
        "page_name": "sales-targets",
        "target": "Pagination",
        "content": "If you have many targets, they'll be split across multiple pages. Use these pagination controls to navigate between pages. You can also change the number of items shown per page.",
        "order": 8,
        "category": HelpStepCategory.NAVIGATION.value
    },
    {
        "page_name": "sales",
        "target": "h2.text-left",
        "content": "Welcome to the Sales Records page! This is where you'll manage all your sales transactions. You can add new sales, view existing ones, and track their status. Let's explore the features.",
        "order": 1,
        "category": HelpStepCategory.INTRODUCTION.value
    },
    {
        "page_name": "sales",
        "target": 'Button[variant="primary"]',
        "content": "Click this 'Add Sale' button to record a new sale. You'll need to enter details like client name, policy type, amount, and other relevant information. Make sure all required fields are filled correctly.",
        "order": 2,
        "category": HelpStepCategory.FEATURE.value
    },
    {
        "page_name": "sales",
        "target": 'Button[variant="info"], Button[variant="warning"], Button[variant="danger"], Button[variant="secondary"]',
        "content": "These status filters help you organize your sales records. Blue shows submitted records, yellow indicates under investigation, and red marks rejected records. The gray button resets all filters.",
        "order": 3,
        "category": HelpStepCategory.NAVIGATION.value
    },
    {
        "page_name": "sales",
        "target": 'DatePicker',
        "content": "Use the date picker to filter sales records by date. You can view sales for specific days, weeks, or months. This is useful for generating reports or tracking sales trends.",
        "order": 4,
        "category": HelpStepCategory.NAVIGATION.value
    },
    {
        "page_name": "sales",
        "target": 'input[name="clientName"]',
        "content": "Search for specific clients by typing their name here. The system will show matching records as you type. This is helpful when you need to find a particular client's sales quickly.",
        "order": 5,
        "category": HelpStepCategory.NAVIGATION.value
    },
    {
        "page_name": "sales",
        "target": "Table",
        "content": "This table displays all your sales records. Each row shows the client name, amount, policy type, status, and other important details. You can sort by any column to organize the data.",
        "order": 6,
        "category": HelpStepCategory.FEATURE.value
    },
    {
        "page_name": "sales",
        "target": 'Button[variant="primary"]',
        "content": "Click the 'View' button to see detailed information about a sale. This includes all transaction details, client information, and any associated documents or notes.",
        "order": 7,
        "category": HelpStepCategory.FEATURE.value
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

def seed_help_steps():
    """Seed the database with help steps."""
    with app.app_context():
        for step_data in help_steps_data:
            try:
                step = HelpStep(**step_data)
                db.session.add(step)
                db.session.commit()
            except IntegrityError:
                db.session.rollback()
                print(f"Step already exists: {step_data['page_name']} - {step_data['order']}")

if __name__ == "__main__":
    seed_help_steps()
