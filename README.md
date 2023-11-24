# GitHub Backup and Restore Tool

This project provides a command-line tool (CLI) written in Python to perform backups of GitHub repositories and resources, as well as to restore these backups.

## Features

- **Repository Backup:** Backs up repositories from a GitHub organization.
- **Resource Backup:** Saves additional information such as labels, issues, and repository details.
- **Backup Restoration:** Allows restoring repositories from generated backups.

## Requirements

- Python 3.x
- Additional dependencies (see `requirements.txt`)

## Installation

1. Clone this repository to your local machine:

    ```bash
    git clone https://github.com/your_username/gh-backup.git
    ```

2. Create and activate a virtual environment:

    ```bash
    cd github_tool
    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3. Install dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

```bash
python gh_repo_backup/backup.py -o ORG_NAME -t ACCESS_TOKEN -d OUTPUT_DIR -r REPO_NAMES -rc -pb
