
from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from github import Github
import os
import argparse

def authenticate_ado(ado_organization_url, ado_pat):
    ado_credentials = BasicAuthentication('', ado_pat)
    return Connection(base_url=ado_organization_url, creds=ado_credentials)

def authenticate_github(github_token):
    return Github(github_token)

def get_ado_repos(ado_connection, project_name):
    return ado_connection.clients.get_git_client().get_repositories(project_name)

def create_github_mirror(github_org, repo_name):
    return github_org.create_repo(
        name=repo_name,
        private=True  
    )

def replicate_repos(ado_org_name, ado_repos, gh_org_name, gh_access_token):
    
    ado_organization_url = "https://dev.azure.com/{ado_org_name}"
    ado_connection = authenticate_ado(ado_organization_url, ado_pat)
    github = authenticate_github(github_token)
    github_org = github.get_organization(github_organization)
    
    projects = ado_connection.clients.get_core_client().get_projects()
    github_org = github.get_organization(github_organization)
    
    for project in projects:
        ado_project_name = project.name
        repos = get_ado_repos(ado_connection, ado_project_name)
        for repo in repos:
            if repos_to_replicate and repo.name not in repos_to_replicate:
                continue  

            github_repo = create_github_mirror(github_org, repo.name)

            local_path = f"./{repo.name}"

            os.system(f'git clone {repo.remote_url} {local_path}')
            os.chdir(local_path)
            os.system(f'git remote add github {github_repo.clone_url}')

            os.system('git push --mirror github')
            os.chdir('..')

if __name__ == "__main__":
        parser = argparse.ArgumentParser(description='Backup ADO repos into GitHub organization.')
        parser.add_argument('-gho', '--gh_org_name', type=str, help='GitHub organization name')
        parser.add_argument('-ght', '--gh_access_token', type=str, help='Github Access Token')
        parser.add_argument('-adoo', '--ado_org_name', type=str, help='ADO org name')
        parser.add_argument('-r', '--repo_names', type=str, nargs='*', help='List of ADO repository names to include in the backup')
        args = parser.parse_args()

        gh_org_name = args.org_name or os.environ.get("GITHUB_ORG")
        gh_access_token = args.access_token or os.environ.get("GITHUB_ACCESS_TOKEN")
        ado_org_name = args.org_name or os.environ.get("ADO_ORG")
        ado_repos = args.repo_names
        
        if gh_org_name is None or gh_access_token is None or ado_org_name is None:
            raise ValueError("Please provide organization name, access token, and the backup.zip path")
        
        replicate_repos(ado_org_name, ado_repos, gh_org_name, gh_access_token)
        
        
        
            

    
 
