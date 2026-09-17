# KHAGATARA Backup and Recovery Procedure

**Document owner:** Khagatara Administrator  
**Version:** 1.0  
**Effective date:** 2026-09-17  
**Review frequency:** At least every 6 months and after a material change to the application or storage architecture

## 1. Purpose

This procedure defines how KHAGATARA application data is backed up and restored for the local-only environment.

## 2. Scope

The procedure covers:

- `data\`
- `docs\`
- Application source code maintained in GitHub

Credential material stored separately under `KHAGATARA-SECURE` is not copied into the application backup or GitHub repository.

## 3. Backup location

Local backup root:

`%USERPROFILE%\KHAGATARA-BACKUPS`

Each backup is stored in a timestamped directory:

`YYYYMMDD-HHMMSS`

## 4. Backup procedure

From the KHAGATARA project root:

```powershell
$backupRoot = "$env:USERPROFILE\KHAGATARA-BACKUPS"
$stamp = Get-Date -Format "yyyyMMdd-HHmmss"
$backup = Join-Path $backupRoot $stamp

New-Item -ItemType Directory -Path $backup -Force | Out-Null
Copy-Item ".\data" "$backup\data" -Recurse -Force
Copy-Item ".\docs" "$backup\docs" -Recurse -Force
```

After backup, verify that the expected files are present and that file sizes are reasonable.

## 5. Recovery test

A restore test must be performed into a separate temporary directory so that the working application is not modified.

```powershell
$restore = "$env:USERPROFILE\KHAGATARA-RESTORE-TEST"

Remove-Item $restore -Recurse -Force -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Path $restore -Force | Out-Null

Copy-Item "$backup\data" "$restore\data" -Recurse -Force
Copy-Item "$backup\docs" "$restore\docs" -Recurse -Force
```

Verify the restored files and compare the restored file count with the source.

## 6. Verified recovery test

On 2026-09-17, a backup was created at:

`C:\Users\ACER\KHAGATARA-BACKUPS\20260917-220244`

A restore test was performed at:

`C:\Users\ACER\KHAGATARA-RESTORE-TEST`

Verification result:

- Original files: 10
- Restored files: 10
- File sizes matched the backup listing
- The working project was not modified by the restore test

## 7. Credential handling

The backup procedure must not copy:

- LWA client secrets
- Refresh tokens
- Private keys
- `.dpapi` credential files
- Other authentication secrets

Credential storage remains outside the repository in the protected `KHAGATARA-SECURE` directory.

## 8. Recovery process

If application data is lost or corrupted:

1. Stop affected application processes if necessary.
2. Identify the most recent known-good backup.
3. Verify the backup contents.
4. Restore the required `data` and `docs` directories.
5. Run the application's existing tests/validation.
6. Confirm the application starts and expected data is readable.
7. Record the recovery event and any corrective action.

## 9. Review

The Khagatara Administrator reviews this procedure at least every six months and whenever there is a material change to the application, storage, credential handling, or deployment model.

## 10. Limitations

This procedure currently documents a local backup and restore process. It does not claim that an off-site backup, automated backup service, or disaster-recovery environment exists.

The GitHub repository provides source-code version history but is not treated as a repository for secrets.
