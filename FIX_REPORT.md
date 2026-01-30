# Fix Report: Backup Error Handling

## Issue
The user encountered a "Backup failed: Unknown error" message. This was caused by the application suppressing specific error details and displaying a generic message when a backup operation failed.

## Fix
Updated `src/addons_profile_manager/cli.py` to:
1.  **Expose Error Details**: Modified `create_backup` to iterate through and display specific `failed_files` and `validation_errors` returned by the backup manager.
2.  **Correct Status Reporting**: Updated `run_interactive` to properly check the return value of `create_backup` and display a failure message if the process did not complete successfully.

## Verification
Please run the manual test again. If the backup fails, the application should now output specific reasons (e.g., "Permission denied", "File not found", "Validation failed"), allowing us to diagnose the root cause.
