import subprocess
import requests
import json
import os
import sys

def get_credentials():
    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True,
        capture_output=True,
        timeout=10
    )
    token = None
    username = None
    for line in proc.stdout.splitlines():
        if line.startswith("password="):
            token = line.split("=", 1)[1]
        elif line.startswith("username="):
            username = line.split("=", 1)[1]
    return username, token

username, token = get_credentials()
print(f"Retrieved credentials for GitHub user: {username}")
if not token:
    print("Error: Could not retrieve GitHub token.")
    sys.exit(1)

headers = {
    "Authorization": f"token {token}",
    "Accept": "application/vnd.github.v3+json",
    "User-Agent": "GitScript"
}

repo_name = "Secure-PDF-Document-Authentication"
repo_url = f"https://api.github.com/repos/{username}/{repo_name}"

# Check if repo exists
check_resp = requests.get(repo_url, headers=headers)
if check_resp.status_code == 200:
    print(f"Repository {repo_name} already exists on GitHub.")
elif check_resp.status_code == 404:
    print(f"Creating repository {repo_name} on GitHub...")
    create_payload = {
        "name": repo_name,
        "description": "Secure PDF Document Authentication Using Cryptographic Hashing and QR Codes (React + FastAPI + PyMuPDF + OpenCV)",
        "private": False,
        "has_issues": True,
        "has_projects": True,
        "has_wiki": True
    }
    create_resp = requests.post("https://api.github.com/user/repos", headers=headers, json=create_payload)
    if create_resp.status_code in [200, 201]:
        print(f"Successfully created repository: {create_resp.json().get('html_url')}")
    else:
        print(f"Failed to create repo: {create_resp.status_code} - {create_resp.text}")
        sys.exit(1)
else:
    print(f"Unexpected status checking repo: {check_resp.status_code}")

# Now configure git and push
def run_git(args):
    print(f"Running: git {' '.join(args)}")
    res = subprocess.run(["git"] + args, capture_output=True, text=True)
    if res.stdout:
        print(res.stdout)
    if res.stderr:
        print(res.stderr)
    return res

run_git(["init"])
run_git(["branch", "-M", "main"])
run_git(["remote", "remove", "origin"])
run_git(["remote", "add", "origin", f"https://github.com/{username}/{repo_name}.git"])
run_git(["add", "."])
run_git(["commit", "-m", "Initial commit: Complete PDF document authentication system with FastAPI backend and React frontend"])

# Push to origin main
push_res = run_git(["push", "-u", "origin", "main", "--force"])
if push_res.returncode == 0:
    print("\nSUCCESS! Successfully pushed to GitHub!")
    print(f"Repo URL: https://github.com/{username}/{repo_name}")
else:
    print("\nPush had non-zero return code. Checking output above.")
