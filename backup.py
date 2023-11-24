import json
import argparse
import shutil

from git import Repo
from git import GitCommandError
from github import BadCredentialsException 
from github import RateLimitExceededException 
from github import Github 

import zipfile
import os
import datetime
import logging

global org_name
global access_token
global output_dir 
    
def github_auth(client_id=None, client_secret=None, access_token=None):
    try:
        if client_id and client_secret:
            g = Github(client_id=client_id, client_secret=client_secret)
        elif access_token:
            g = Github(access_token)
        else:
            raise ValueError("No auth parameters provided.")

        return g

    except BadCredentialsException as e:
        print("Github Invalid Credentials:", e)
    except RateLimitExceededException as e:
        print("Github Rate limit exceeded.", e)
    except Exception as e:
        print("Github Auth issues:", e)

    return None
def create_folder(path):
    os.makedirs(path, exist_ok=True)

def save_data_to_json(data, output_file):
    try:
        with open(output_file, "w") as file:
            json.dump(data, file, indent=4)
    except Exception as e:
        print(f"Error while saving data to JSON: {e}")

def compress_directory(directory):
    current_date = datetime.datetime.now()
    date_str = current_date.strftime('%Y-%m-%d')
    zip_file_name = f'{directory}_{date_str}.zip'
    with zipfile.ZipFile(zip_file_name, 'w', zipfile.ZIP_DEFLATED) as zip_file:
        for root, subdirs, files in os.walk(directory):
            for file in files:
                full_path = os.path.join(root, file)
                relative_path = os.path.relpath(full_path, directory)
                zip_file.write(full_path, relative_path)

    print(f'ZIP file created: {zip_file_name}')
    
def backup_labels(repo, repo_folder):

    try:
        labels = repo.get_labels()
        labels_data = [{"name": label.name, "color": label.color} for label in labels]
        output_file = os.path.join(repo_folder, "labels.json")
        save_data_to_json(labels_data, output_file)
        
    except Exception as e:
        print(f"Error backing up labels for the repository {repo.name}: {e}")
    logging.info("END Backing up repo Labels...")


def backup_issues(repo, repo_folder):

    try:
        issues = repo.get_issues(state="all")
        issues_data = []
        for issue in issues:
            issue_info = {
                "number": issue.number,
                "title": issue.title,
                "body": issue.body,
                "state": issue.state,
                "created_at": issue.created_at.isoformat(),
                "updated_at": issue.updated_at.isoformat(),
                "closed_at": issue.closed_at.isoformat() if issue.closed_at else None,
                "user": issue.user.login,
                "labels": [label.name for label in issue.get_labels()]
            }
            issues_data.append(issue_info)
            
        output_file = os.path.join(repo_folder, "issues.json")
        save_data_to_json(issues_data, output_file)
        
    except Exception as e:
        print(f"Error backing up issues for the repository {repo.name}: {e}")

def backup_repository(repo, repo_folder):
    
    repo_data = {
        "name": repo.name,
        "description": repo.description,
        "website": repo.homepage,
        "language": repo.language,
        "created_at": repo.created_at.isoformat(),
        "updated_at": repo.updated_at.isoformat()
    }
    
    output_file = os.path.join(repo_folder, "repository.json")
    save_data_to_json(repo_data, output_file)
        
        
def clone_repository(repo, repo_backup_folder, repo_clone, token):
    logging.info("Cloning repository...")
    logging.info(f"Parameters: repo_folder={repo_backup_folder}, repo_clone={repo_clone}, repo_name={repo.name}")

    if repo_clone:
        now = datetime.datetime.now()
        subfolder_name = f"repo_cloned_{repo.name}_{now.strftime('%Y-%m-%d_%H-%M-%S')}"
        subfolder_path = os.path.join(repo_backup_folder, subfolder_name)
        
        try:
            os.makedirs(subfolder_path, exist_ok=True)
            
            clone_url_with_token = f"https://{token}@github.com/{repo.full_name}.git"
            repo_temp = Repo.clone_from(clone_url_with_token, subfolder_path, no_single_branch=True)
            
            repo_temp.git.archive("--format", "zip", "--output", f"{subfolder_path}.zip", "HEAD")
            logging.info(f"Repository cloned successfully to {subfolder_path}")
            
            if os.listdir(subfolder_path):
                logging.info("Repository folder contains files.")
            else:
                logging.warning("Repository folder is empty.")
                
            return subfolder_path 
            
        except GitCommandError as e:
            logging.error(f"Error during repository cloning: {str(e)}")
            return None 
      
def backup_repository_resources(repo, org_folder, repo_clone, access_token, publish_backup):
    repo_backup_folder = os.path.join(org_folder, repo.name)
    create_folder(repo_backup_folder)

    backup_labels(repo, repo_backup_folder)
    backup_issues(repo, repo_backup_folder)
    backup_repository(repo, repo_backup_folder)
    if repo_clone:
        cloned_folder = clone_repository(repo, repo_backup_folder, repo_clone,access_token )
        compress_directory(repo_backup_folder)
        shutil.rmtree(os.path.join(repo_backup_folder, f"repo_cloned_{repo.name}"))
        if os.path.exists(cloned_folder):
            shutil.rmtree(cloned_folder)
    if publish_backup: 
       logging.info("TODO. Need to implement publish_backup")         

def backup_organization_resources(org_name, access_token, output_dir, repo_names=None, repo_clone=False, publish_backup=False):
    logging.info("INIT  backup_organization_resources Method")
    g = github_auth(access_token=access_token)

    try:
        org = g.get_organization(org_name)
        logging.info("Getting organization details "+ org_name)
    except Exception as e:
        print(f"Error getting the organization: {e}")
        return

    org_folder = os.path.join(output_dir, org_name)
    create_folder(org_folder)

    org_data = {
        "name": org_name,
        "description": org.description,
        "website": org.blog,
        "location": org.location,
        "repositories": []
    }

    try:
        repositories = org.get_repos()
        logging.info("Getting repositories for the organization " + str(repo_names))
    except Exception as e:
        print(f"Error getting the list of repositories: {e}")
        return

    for repo in repositories:
        if repo_names is None or repo.name in repo_names:
            try:
                backup_repository_resources(repo, org_folder, repo_clone, access_token, publish_backup)
                org_data["repositories"].append(repo.name)
            except Exception as e:
                print(f"Error backing up the repository {repo.name}: {e}")


    with open(os.path.join(org_folder, "organization.json"), "w") as org_file:
        org_file.write(json.dumps(org_data, indent=4))
        
    logging.info("END backup_organization_resources Method")


if __name__ == "__main__":
    
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        
        parser = argparse.ArgumentParser(description='Backup GitHub organization resources.')
        parser.add_argument('-o', '--org_name', type=str, help='GitHub organization name')
        parser.add_argument('-t', '--access_token', type=str, help='GitHub access token')
        parser.add_argument('-d', '--output_dir', type=str, help='Output directory for backup')
        parser.add_argument('-r', '--repo_names', type=str, nargs='*', help='List of repository names to include in the backup')
        parser.add_argument('-rc', '--repo_clone', action='store_true', help='Including whole repo clone as part of the backup')
        parser.add_argument('-pb', '--publish_backup', action='store_true', help='Publish backup as a zip file in remote storage')
        args = parser.parse_args()


        org_name = args.org_name or os.environ.get("GITHUB_ORG")
        access_token = args.access_token or os.environ.get("GITHUB_ACCESS_TOKEN")
        output_dir = args.output_dir or os.environ.get("GITHUB_BACKUP_DIR")
        repo_names = args.repo_names
        repo_clone = args.repo_clone
        publish_backup = args.publish_backup
        
        if org_name is None or access_token is None or output_dir is None:
            raise ValueError("Please provide organization name, access token, and output directory.")
        
        backup_organization_resources(org_name, access_token, output_dir, repo_names, repo_clone, publish_backup)
