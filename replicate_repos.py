from azure.devops.connection import Connection
from msrest.authentication import BasicAuthentication
from github import Github
import os
import argparse
import azure.devops.exceptions

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

def get_ado_repos(ado_connection, project_name):
    return ado_connection.clients.get_git_client().get_repositories(project_name)

def replicate_repos(ado_org_name, ado_project_name, ado_access_token, ado_repos, gh_org_name, gh_access_token):
    ado_organization_url = f"https://dev.azure.com/{ado_org_name}"

    try:
        ado_connection = authenticate_ado(ado_organization_url, ado_access_token)
        print(f"Authenticated to Azure DevOps: {ado_organization_url}")
    except Exception as e:
        print(f"Error authenticating to Azure DevOps: {e}")
        return

    try:
        repos = get_ado_repos(ado_connection, ado_project_name)
        print(f"Found {len(repos)} repositories in Azure DevOps project: {ado_project_name}")
    except azure.devops.exceptions.AzureDevOpsClientRequestError as e:
        print(f"Error fetching repositories from Azure DevOps: {e}")
        return

    if not ado_repos: 
        ado_repos = [repo.name for repo in repos]

    try:
        ghAuth = authenticate_github(gh_access_token)
        github_org = ghAuth.get_organization(gh_org_name)
        print(f"Authenticated to GitHub organization: {gh_org_name}")
    except Exception as e:
        print(f"Error authenticating to GitHub: {e}")
        return

    for repo in repos:
        if ado_repos and repo.name not in ado_repos:
            print(f"Skipping repository: {repo.name}")
            continue

        print(f"Creating GitHub mirror for repository: {repo.name}")
        try:
            github_repo = create_github_mirror(github_org, repo.name)
        except Exception as e:
            print(f"Error creating GitHub repository: {e}")
            continue

        print(f"Adding topics to GitHub repo: {github_repo.full_name}")
        github_repo.add_to_topics(f"ADO Repo URL: {repo.remote_url}")
        github_repo.add_to_topics(f"ADO Project: {ado_project_name}")
        github_repo.add_to_topics(f"ADO Repo Name: {repo.name}")

        local_path = f"./{repo.name}"

        print(f"Cloning Azure DevOps repo to local path: {local_path}")
        os.system(f'git clone {repo.remote_url} {local_path}')
        os.chdir(local_path)
        os.system(f'git remote add github {github_repo.clone_url}')

        print("Pushing changes to GitHub repo")
        os.system('git push --mirror github')
        os.chdir('..')



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Backup ADO repos into GitHub organization.')
    parser.add_argument('-adoo', '--ado_org_name', type=str, help='ADO org name')
    parser.add_argument('-adop', '--ado_project_name', type=str, help='ADO pro name')
    parser.add_argument('-adot', '--ado_access_token', type=str, help='ADO Access Token')
    parser.add_argument('-r', '--repo_names', type=str, nargs='*', help='List of ADO repository names to include in the backup')
    
    parser.add_argument('-gho', '--gh_org_name', type=str, help='GitHub organization name')
    parser.add_argument('-ght', '--gh_access_token', type=str, help='Github Access Token')
   
    args = parser.parse_args()

    ado_org_name = args.ado_org_name or os.environ.get("ADO_ORG")
    ado_project_name = args.ado_project_name or os.environ.get("ADO_PROJECT_NAME")
    ado_access_token = args.ado_access_token or os.environ.get("ADO_ACCESS_TOKEN")
    ado_repos = args.repo_names
    
    gh_org_name = args.gh_org_name or os.environ.get("GITHUB_ORG")
    gh_access_token = args.gh_access_token or os.environ.get("GITHUB_ACCESS_TOKEN")

    if gh_org_name is None or gh_access_token is None or ado_org_name is None or ado_access_token is None or ado_project_name is None:  
        raise ValueError("Please provide organization name, access token, and the backup.zip path")

    replicate_repos(ado_org_name, ado_project_name, ado_access_token, ado_repos, gh_org_name, gh_access_token)
