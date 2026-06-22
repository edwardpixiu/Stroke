# Stroke

Stroke MI Model Program, including EEG and MRI modules.

## Pull and Push Progress

本文档用于说明如何在本地桌面或服务器上配置 Git，并将项目代码同步到 GitHub 仓库。

## How to Pull the Code to Your Desktop

### 1. Check Whether Git Is Available

Open a terminal and run:

```bash
git --version
```

If a Git version is printed, Git is already installed and you can continue.

Example:

```text
git version 2.43.0
```

If Git is not installed, install it first:

- Windows: <https://git-scm.com/download/win>
- Ubuntu:

```bash
sudo apt update
sudo apt install git -y
```

## Git Environment Configuration

Configure your GitHub email and username:

```bash
git config --global user.email "your_email@example.com"
git config --global user.name "your_github_username"
```

Check current configuration:

```bash
git config --global --list
```

## Initialize a Local Repository

Move into your local workspace:

```bash
cd /path/to/your_local_workspace
```

Initialize the repository:

```bash
git init
```

## Connect Local Repository to GitHub

Add the remote GitHub repository:

```bash
git remote add origin https://github.com/your_username/your_repository.git
```

Check whether the remote repository is configured correctly:

```bash
git remote -v
```

## Upload Local Files to GitHub

Add all files:

```bash
git add .
```

Commit changes:

```bash
git commit -m "Initial commit"
```

Push to the online branch:

```bash
git push -u origin main
```

If your online branch is named differently, replace `main` with the correct branch name:

```bash
git push -u origin <online_branch_name>
```

## Pull Code from GitHub

If the repository already exists online, clone it directly:

```bash
git clone https://github.com/your_username/your_repository.git
```

Move into the project directory:

```bash
cd your_repository
```

Pull the latest changes:

```bash
git pull origin main
```

## Other Questions

### GitHub Authentication Permission Error

Sometimes GitHub may raise a permission or authentication error during `git push`.

GitHub no longer supports password-based Git authentication over HTTPS. Use a Personal Access Token instead.

Steps:

1. Log in to GitHub.
2. Click the avatar in the upper-right corner.
3. Go to `Settings`.
4. Scroll down and open `Developer settings`.
5. Open `Personal access tokens`.
6. Select `Tokens (classic)`.
7. Click `Generate new token (classic)`.
8. Set a token name, such as `Ubuntu` or `LocalGit`.
9. Set expiration. If needed, choose `No expiration`.
10. Select the `repo` permission.
11. Generate the token and copy it immediately.

When running:

```bash
git push
```

GitHub may ask for:

```text
Username:
Password:
```

Use:

```text
Username: your GitHub username
Password: your Personal Access Token
```

### Save Git Credentials

To avoid entering the token every time:

```bash
git config --global credential.helper store
```

Then run `git push` once and enter your username and token. Git will store the credential locally.

> Note: `credential.helper store` saves credentials as plain text on the machine. Use it only on trusted personal machines or servers.

## Large File Warning

GitHub blocks files larger than 100 MB in normal Git repositories, and large files around 200 MB or more should not be committed directly.

For EEG/MRI projects, large raw data files should usually be excluded from Git.

Create or edit `.gitignore` in the project root:

```bash
cat > .gitignore <<'EOF'
*.eeg
*.vhdr
*.vmrk
*.nii
*.nii.gz
*.zip
*.tar.gz
*.7z
*.mat
*.h5
*.hdf5
rawdata/
derivatives/
outputs/
logs/
tmp/
EOF
```

Add and commit `.gitignore`:

```bash
git add .gitignore
git commit -m "Update .gitignore"
```

## Recommended Project Upload Workflow

Use this workflow when uploading a local project for the first time:

```bash
cd /path/to/your_project

git init
git config --global user.email "your_email@example.com"
git config --global user.name "your_github_username"

git remote add origin https://github.com/your_username/your_repository.git

git add .
git commit -m "Initial project upload"
git push -u origin main
```

If the branch does not exist or your default branch is `master`, check current branch:

```bash
git branch
```

Rename current branch to `main` if needed:

```bash
git branch -M main
```

Then push again:

```bash
git push -u origin main
```

## Common Commands

Check repository status:

```bash
git status
```

View commit history:

```bash
git log --oneline
```

Pull latest code:

```bash
git pull origin main
```

Add modified files:

```bash
git add .
```

Commit changes:

```bash
git commit -m "Update code"
```

Push changes:

```bash
git push
```

Check remote repository:

```bash
git remote -v
```

## Notes

- Do not commit raw EEG or MRI data directly to GitHub.
- Use `.gitignore` before the first commit to avoid uploading large data files.
- Use GitHub Personal Access Token instead of account password.
- If large files must be versioned, consider Git LFS.
- Keep source code, configuration files, and lightweight documentation in Git.
- Keep raw data, intermediate outputs, checkpoints, and logs outside Git unless explicitly needed.
