# Put this broadcast kit on your own GitHub

First, create a **new, empty repository** named `daze-broadcast-kit` on GitHub. Choose public if the team should download the ZIP without a GitHub login; choose private if only invited members should access it. **Do not** initialize the new repository with a README, license, or .gitignore; this source ZIP already has a README and .gitignore.

Extract the source ZIP on the computer where Git for Windows is installed. Open PowerShell in the extracted source folder, making sure the `daze_telemetry`, `packaging`, and `.github` folders are inside your current directory.

```powershell
git init
git branch -M main
git add -A
git commit -m "Daze Broadcast Kit v1.3 - local telemetry overlay"
git remote add origin https://github.com/YOUR_GITHUB_USERNAME/daze-broadcast-kit.git
git push -u origin main
```

Replace `YOUR_GITHUB_USERNAME` with your GitHub account name. The workflow runs on pushes to `main`. On GitHub, open **Actions → Build Daze Broadcast Kit for Windows** and confirm the workflow passes. Download its **Daze-Broadcast-Kit-v1.3-Windows** artifact to test the first Windows build.

After you have tested it in OBS with iRacing and spectator mode, create a stable team download:

```powershell
git tag v1.3.0
git push origin v1.3.0
```

That tag triggers the workflow again and, if GitHub Actions has `contents: write` permission, creates **Releases → v1.3.0** with the ready-to-install Windows ZIP. Share the **Release ZIP**, not this source archive, with team members.

Do not store YouTube stream keys, Discord secrets, or credentials in this repository.
