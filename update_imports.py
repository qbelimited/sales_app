import os
import re

def update_imports(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Replace from extensions import db with from extensions import db
    new_content = re.sub(
        r'from app import (db, logger|db|logger)',
        'from extensions import db',
        content
    )

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

def main():
    # Get all Python files in the project
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                file_path = os.path.join(root, file)
                update_imports(file_path)

if __name__ == '__main__':
    main()
