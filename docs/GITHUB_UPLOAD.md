# Upload this repository to a personal GitHub account

The release package is intentionally prepared without the earlier development commit history. Create the first commit using your own Git identity.

## 1. Create an empty GitHub repository

On GitHub, create a repository such as `three-gorges-microseismic-catalog`. Keep it **Private** until model/data redistribution and coauthor approvals are complete. Do not initialize the remote repository with a README, `.gitignore`, or license because those files already exist locally.

## 2. Configure Git identity locally

```bash
git config --global user.name "YOUR NAME"
git config --global user.email "YOUR_GITHUB_NOREPLY_OR_EMAIL"
```

## 3. Create the first commit

From the repository root:

```bash
git status
git commit -m "Initial public reproducibility release"
```

The Git-ready package has already staged all release files. If you use the source-only package instead, run `git init -b main` and `git add .` first.

## 4. Connect the GitHub remote and push

Replace `<USER>` with your GitHub username:

```bash
git remote add origin https://github.com/<USER>/three-gorges-microseismic-catalog.git
git push -u origin main
```

GitHub no longer accepts account passwords for Git operations over HTTPS; authenticate using Git Credential Manager, a personal access token when requested by your Git client, or SSH.

## 5. Before switching the repository to Public

Complete `docs/RELEASE_CHECKLIST.md`, especially checkpoint/data redistribution approval, coauthor approval, and the final GMT Figure 6 rerun. Then update `CITATION.cff` with the repository URL and later the archival DOI.
