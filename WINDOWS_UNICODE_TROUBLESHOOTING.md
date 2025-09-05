# Windows Unicode Troubleshooting

This guide helps resolve UnicodeDecodeError and encoding issues on Windows when running PostgreSQL/Alembic with Python.

## Quick checklist
- Set system-wide environment variables (restart terminal afterwards):
  - `setx PGCLIENTENCODING UTF8`
  - `setx PYTHONIOENCODING utf-8`
  - `setx PYTHONUTF8 1`
- Use UTF-8 in the current PowerShell session:
  - `chcp 65001`
  - `$OutputEncoding = [Console]::OutputEncoding = [Text.UTF8Encoding]::UTF8`
- Ensure `.env` is saved as UTF-8 without BOM.
- Check prestart logs: it prints `server_encoding` and `client_encoding` before migrations.
- If Alembic autogenerate crashes, run migrations from WSL/Git Bash or rely on provided manual migration files.

## Prestart migration helper
Our container runs `server/scripts/prestart.py`:
- Sets `PGCLIENTENCODING=UTF8`
- Verifies server/client encodings via psycopg2
- Retries `alembic upgrade head` with backoff

If you see encoding mismatches, fix the DB cluster encoding or ensure the client variables above are set, then rerun.
