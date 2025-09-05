#!/usr/bin/env python3
"""
EduAnalytics Migration Management CLI

A command-line interface for managing database migrations with safety features.
"""

import asyncio
import click
import sys
import os
from pathlib import Path
from typing import Optional

# Add the server directory to Python path
server_dir = Path(__file__).parent.parent / "server"
sys.path.insert(0, str(server_dir))

from app.services.migration_manager import migration_manager
from app.core.config import settings


@click.group()
@click.option('--verbose', '-v', is_flag=True, help='Enable verbose output')
@click.pass_context
def cli(ctx, verbose):
    """EduAnalytics Migration Management CLI."""
    ctx.ensure_object(dict)
    ctx.obj['verbose'] = verbose
    
    if verbose:
        click.echo("Verbose mode enabled")


@cli.command()
@click.pass_context
def status(ctx):
    """Show current migration status."""
    async def _status():
        click.echo("🔍 Checking migration status...")
        
        status_info = await migration_manager.get_migration_status()
        
        if "error" in status_info:
            click.echo(f"❌ Error: {status_info['error']}", err=True)
            return
        
        current = status_info.get("current_revision", "None")
        pending = status_info.get("total_pending", 0)
        high_risk = status_info.get("high_risk_count", 0)
        backup_available = status_info.get("backup_available", False)
        
        click.echo(f"📊 Migration Status:")
        click.echo(f"   Current revision: {current}")
        click.echo(f"   Pending migrations: {pending}")
        click.echo(f"   High-risk migrations: {high_risk}")
        click.echo(f"   Backup available: {'✅' if backup_available else '❌'}")
        
        if pending > 0:
            click.echo("\n📋 Pending migrations:")
            for migration in status_info.get("pending_migrations", []):
                risk_icon = {"low": "🟢", "medium": "🟡", "high": "🟠", "critical": "🔴"}.get(migration["risk_level"], "❓")
                click.echo(f"   {risk_icon} {migration['revision_id']}: {migration['description']}")
                if ctx.obj['verbose']:
                    click.echo(f"      Risk: {migration['risk_level']}, Duration: ~{migration['estimated_duration']}s")
    
    asyncio.run(_status())


@cli.command()
@click.option('--target', '-t', default='head', help='Target revision (default: head)')
@click.pass_context
def dry_run(ctx, target):
    """Perform a dry run of migrations."""
    async def _dry_run():
        click.echo(f"🧪 Performing dry run to {target}...")
        
        result = await migration_manager.dry_run_migration(target)
        
        if result["success"]:
            click.echo("✅ Dry run completed successfully!")
            if ctx.obj['verbose'] and result.get("migration_output"):
                click.echo("\n📄 Migration output:")
                click.echo(result["migration_output"])
        else:
            click.echo(f"❌ Dry run failed: {result.get('error', 'Unknown error')}", err=True)
            sys.exit(1)
    
    asyncio.run(_dry_run())


@cli.command()
@click.option('--target', '-t', default='head', help='Target revision (default: head)')
@click.option('--no-backup', is_flag=True, help='Skip backup creation')
@click.option('--force', is_flag=True, help='Force migration even if high-risk')
@click.option('--dry-run-first', is_flag=True, default=True, help='Perform dry run first (default: true)')
@click.pass_context
def upgrade(ctx, target, no_backup, force, dry_run_first):
    """Upgrade database to target revision."""
    async def _upgrade():
        click.echo(f"🚀 Upgrading database to {target}...")
        
        # Check status first
        status_info = await migration_manager.get_migration_status()
        pending = status_info.get("total_pending", 0)
        high_risk = status_info.get("high_risk_count", 0)
        
        if pending == 0:
            click.echo("✅ No pending migrations to apply")
            return
        
        # Warn about high-risk migrations
        if high_risk > 0 and not force:
            click.echo(f"⚠️  Warning: {high_risk} high-risk migrations detected!")
            click.echo("Use --force to proceed or review migrations first.")
            if not click.confirm("Do you want to continue?"):
                click.echo("Migration cancelled")
                return
        
        # Perform dry run first if requested
        if dry_run_first:
            click.echo("🧪 Performing dry run first...")
            dry_run_result = await migration_manager.dry_run_migration(target)
            if not dry_run_result["success"]:
                click.echo(f"❌ Dry run failed: {dry_run_result.get('error')}", err=True)
                click.echo("Aborting migration")
                sys.exit(1)
            click.echo("✅ Dry run successful, proceeding with migration...")
        
        # Perform actual migration
        result = await migration_manager.upgrade_with_safety(
            target_revision=target,
            create_backup=not no_backup,
            force=force
        )
        
        if result.success:
            click.echo(f"✅ Migration completed successfully in {result.duration:.2f}s")
            if result.backup_path:
                click.echo(f"💾 Backup created: {result.backup_path}")
        else:
            click.echo(f"❌ Migration failed: {result.error}", err=True)
            if result.backup_path:
                click.echo(f"💾 Backup available for rollback: {result.backup_path}")
            sys.exit(1)
    
    asyncio.run(_upgrade())


@cli.command()
@click.option('--target', '-t', required=True, help='Target revision to rollback to')
@click.option('--no-backup', is_flag=True, help='Skip backup creation')
@click.pass_context
def rollback(ctx, target, no_backup):
    """Rollback database to a specific revision."""
    async def _rollback():
        click.echo(f"⏪ Rolling back database to {target}...")
        
        # Confirm rollback
        if not click.confirm(f"Are you sure you want to rollback to {target}?"):
            click.echo("Rollback cancelled")
            return
        
        result = await migration_manager.rollback_migration(
            target_revision=target,
            create_backup=not no_backup
        )
        
        if result.success:
            click.echo(f"✅ Rollback completed successfully in {result.duration:.2f}s")
            if result.backup_path:
                click.echo(f"💾 Backup created: {result.backup_path}")
        else:
            click.echo(f"❌ Rollback failed: {result.error}", err=True)
            sys.exit(1)
    
    asyncio.run(_rollback())


@cli.command()
@click.option('--revision', '-r', default='manual', help='Revision ID for backup naming')
def backup(revision):
    """Create a manual database backup."""
    async def _backup():
        click.echo(f"💾 Creating database backup for revision {revision}...")
        
        try:
            backup_path = await migration_manager.backup_manager.create_backup(revision)
            click.echo(f"✅ Backup created successfully: {backup_path}")
        except Exception as e:
            click.echo(f"❌ Backup failed: {str(e)}", err=True)
            sys.exit(1)
    
    asyncio.run(_backup())


@cli.command()
@click.option('--limit', '-l', default=10, help='Number of backups to show')
def list_backups(limit):
    """List available database backups."""
    backups = migration_manager.backup_manager.list_backups()
    
    if not backups:
        click.echo("📦 No backups found")
        return
    
    click.echo(f"📦 Available backups (showing last {min(limit, len(backups))}):")
    
    for backup in backups[:limit]:
        size_mb = backup["size"] / 1024 / 1024
        click.echo(f"   📄 {backup['revision']}_{backup['timestamp']}")
        click.echo(f"      Path: {backup['path']}")
        click.echo(f"      Size: {size_mb:.2f} MB")
        click.echo(f"      Created: {backup['created_at']}")
        click.echo()


@cli.command()
@click.argument('backup_path')
def restore(backup_path):
    """Restore database from a backup file."""
    async def _restore():
        click.echo(f"🔄 Restoring database from {backup_path}...")
        
        # Confirm restore
        if not click.confirm("⚠️  This will overwrite the current database. Are you sure?"):
            click.echo("Restore cancelled")
            return
        
        try:
            success = await migration_manager.backup_manager.restore_backup(backup_path)
            if success:
                click.echo("✅ Database restored successfully")
            else:
                click.echo("❌ Database restore failed", err=True)
                sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Restore failed: {str(e)}", err=True)
            sys.exit(1)
    
    asyncio.run(_restore())


@cli.command()
def validate():
    """Validate migration integrity and safety."""
    async def _validate():
        click.echo("🔍 Validating migration integrity...")
        
        # Check migration status
        status_info = await migration_manager.get_migration_status()
        
        if "error" in status_info:
            click.echo(f"❌ Validation error: {status_info['error']}", err=True)
            return
        
        # Validation checks
        issues = []
        warnings = []
        
        pending = status_info.get("pending_migrations", [])
        high_risk = [m for m in pending if m["risk_level"] in ["high", "critical"]]
        no_rollback = [m for m in pending if not m.get("rollback_available", False)]
        
        if high_risk:
            warnings.append(f"⚠️  {len(high_risk)} high-risk migrations pending")
        
        if no_rollback:
            warnings.append(f"⚠️  {len(no_rollback)} migrations without rollback capability")
        
        if not status_info.get("backup_available", False) and pending:
            warnings.append("⚠️  No backups available with pending migrations")
        
        # Show results
        if not issues and not warnings:
            click.echo("✅ All validation checks passed")
        else:
            if warnings:
                click.echo("⚠️  Validation warnings:")
                for warning in warnings:
                    click.echo(f"   {warning}")
            
            if issues:
                click.echo("❌ Validation issues:")
                for issue in issues:
                    click.echo(f"   {issue}")
    
    asyncio.run(_validate())


@cli.command()
@click.option('--limit', '-l', default=20, help='Number of revisions to show')
def history(limit):
    """Show migration history."""
    click.echo(f"📚 Migration history (last {limit} revisions):")
    
    try:
        from alembic.config import Config
        from alembic.script import ScriptDirectory
        
        # Get Alembic config
        alembic_cfg = Config("alembic.ini")
        script_dir = ScriptDirectory.from_config(alembic_cfg)
        
        # Get revision history
        count = 0
        for revision in script_dir.walk_revisions():
            click.echo(f"   📄 {revision.revision}: {revision.doc or 'No description'}")
            if revision.down_revision:
                click.echo(f"      ⬅️  From: {revision.down_revision}")
            
            count += 1
            if count >= limit:
                break
            
    except Exception as e:
        click.echo(f"❌ Failed to get history: {str(e)}", err=True)


if __name__ == '__main__':
    # Change to server directory
    os.chdir(server_dir)
    cli()
