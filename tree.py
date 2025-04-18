import os
import sys


def generate_folder_structure(path, exclusions, output_file):
    """
    Generate folder structure representation and write it to the output file.

    Args:
        path (str): Base directory path to generate the structure from.
        exclusions (list): Directories to exclude from the structure.
        output_file (str): File to write the folder structure to.
    """
    try:
        with open(output_file, 'w') as f:
            for root, dirs, files in os.walk(path):
                for exclusion in exclusions:
                    if exclusion in dirs:
                        dirs.remove(exclusion)
                level = root.replace(path, '').count(os.sep)
                indent = ' ' * 4 * (level)
                f.write('{}{}/\n'.format(indent, os.path.basename(root)))
                subindent = ' ' * 4 * (level + 1)
                for file in files:
                    f.write('{}{}\n'.format(subindent, file))
    except Exception as e:
        print(f"An error occurred: {e}")
        sys.exit(1)


if __name__ == "__main__":
    # Get the directory of the script as the base path
    base_path = os.path.dirname(os.path.abspath(__file__))
    exclusions = ['venv', '__pycache__', 'instance', '.git', 'static', '.mypy_cache', 'logs', 'node_modules']
    output_file = 'docs/app_structure.txt'
    generate_folder_structure(base_path, exclusions, output_file)
