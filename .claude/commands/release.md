---
allowed-tools: Read, Edit, Bash(git add:*), Bash(git status:*), Bash(git commit:*), Bash(git checkout:*), Bash(git push:*), Bash(gh issue create:*), Bash(gh pr create:*), Bash(uv version --short)
description: Execute the release process for VoxVibe
---

Your task is to run the complete release process for VoxVibe.

The current version is: !`cd app && uv version --short`

The version update should be: $ARGUMENTS

Where the update is one of:
- `major` - increment major version (1.0.0 → 2.0.0)
- `minor` - increment minor version (1.0.0 → 1.1.0) 
- `bugfix` - increment patch version (1.0.0 → 1.0.1)
- Specific version number (e.g., `1.2.3`)

The process you must follow is:
1. Verify working tree is clean.
2. Create a github issue for updating the version number
3. Create a branch in the form of `release/vX.Y.Z`
4. Update version in app/pyproject.toml.
5. Read the version number in extension/metadata.json and increment by 1.
6. Run `uv lock` to update the lock file.
7. Commit changes to the branch and push to GitHub.
8. Create a PR for the release branch.

The user will complete the remaining steps:
1. Merge the PR into main.
2. Check out main and pull the latest changes.
3. Run `make release` to create the release package.
4. Push the new release tag to trigger GitHub Actions release.

Just remind them to do the remaining steps.