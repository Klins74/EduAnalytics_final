#!/bin/bash
# Production-safe database migration script

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
BACKUP_DIR="${BACKUP_DIR:-/backups}"
MIGRATION_TIMEOUT="${MIGRATION_TIMEOUT:-600}"  # 10 minutes

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Functions
log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
    exit 1
}

# Help function
show_help() {
    cat << EOF
Production Database Migration Script

Usage: $0 [OPTIONS] COMMAND

Commands:
    status          Show migration status
    validate        Validate migration safety
    backup          Create database backup
    dry-run         Perform migration dry run
    migrate         Run migrations with full safety checks
    rollback        Rollback to specific revision
    list-backups    List available backups

Options:
    --target REV    Target revision (default: head)
    --force         Force migration (skip safety checks)
    --no-backup     Skip backup creation
    --maintenance   Enable maintenance mode
    --timeout SEC   Migration timeout in seconds (default: 600)
    -h, --help      Show this help

Environment Variables:
    DATABASE_URL              Database connection string
    BACKUP_DIR               Backup directory (default: /backups)
    MIGRATION_TIMEOUT        Timeout in seconds (default: 600)
    MAINTENANCE_PAGE_URL     URL to show during maintenance

Examples:
    $0 status
    $0 validate
    $0 backup
    $0 dry-run --target head
    $0 migrate --target head --maintenance
    $0 rollback --target abc123

EOF
}

# Parse arguments
COMMAND=""
TARGET_REVISION="head"
FORCE=false
NO_BACKUP=false
MAINTENANCE_MODE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        status|validate|backup|dry-run|migrate|rollback|list-backups)
            COMMAND="$1"
            shift
            ;;
        --target)
            TARGET_REVISION="$2"
            shift 2
            ;;
        --force)
            FORCE=true
            shift
            ;;
        --no-backup)
            NO_BACKUP=true
            shift
            ;;
        --maintenance)
            MAINTENANCE_MODE=true
            shift
            ;;
        --timeout)
            MIGRATION_TIMEOUT="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            error "Unknown option: $1"
            ;;
    esac
done

if [[ -z "$COMMAND" ]]; then
    error "Command required. Use --help for usage information."
fi

# Validate environment
if [[ -z "$DATABASE_URL" ]]; then
    error "DATABASE_URL environment variable is required"
fi

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Change to project root
cd "$PROJECT_ROOT"

# Migration management functions
check_migration_status() {
    log "Checking migration status..."
    
    python3 scripts/manage-migrations.py status
    return $?
}

validate_migrations() {
    log "Validating migration safety..."
    
    python3 scripts/manage-migrations.py validate
    return $?
}

create_backup() {
    log "Creating database backup..."
    
    if [[ "$NO_BACKUP" == true ]]; then
        warn "Backup creation skipped (--no-backup flag)"
        return 0
    fi
    
    TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
    BACKUP_NAME="production_${TARGET_REVISION}_${TIMESTAMP}"
    
    python3 scripts/manage-migrations.py backup --revision "$BACKUP_NAME"
    
    if [[ $? -eq 0 ]]; then
        log "Backup created successfully"
        echo "$BACKUP_NAME" > /tmp/last_backup_name
        return 0
    else
        error "Backup creation failed"
    fi
}

perform_dry_run() {
    log "Performing migration dry run..."
    
    timeout "$MIGRATION_TIMEOUT" python3 scripts/manage-migrations.py dry-run --target "$TARGET_REVISION"
    
    if [[ $? -eq 0 ]]; then
        log "Dry run completed successfully"
        return 0
    else
        error "Dry run failed"
    fi
}

enable_maintenance_mode() {
    if [[ "$MAINTENANCE_MODE" == true ]]; then
        log "Enabling maintenance mode..."
        
        # Create maintenance flag file
        touch /tmp/maintenance_mode
        
        # If using nginx, you can reload configuration to serve maintenance page
        if command -v nginx &> /dev/null; then
            log "Reloading nginx for maintenance mode..."
            nginx -s reload || warn "Failed to reload nginx"
        fi
        
        # Wait a moment for connections to drain
        sleep 5
    fi
}

disable_maintenance_mode() {
    if [[ "$MAINTENANCE_MODE" == true ]]; then
        log "Disabling maintenance mode..."
        
        # Remove maintenance flag file
        rm -f /tmp/maintenance_mode
        
        # Reload nginx to serve application
        if command -v nginx &> /dev/null; then
            log "Reloading nginx to resume normal operation..."
            nginx -s reload || warn "Failed to reload nginx"
        fi
    fi
}

run_migration() {
    log "Running database migration to $TARGET_REVISION..."
    
    # Build migration command
    MIGRATION_CMD="python3 scripts/manage-migrations.py upgrade --target $TARGET_REVISION"
    
    if [[ "$NO_BACKUP" == true ]]; then
        MIGRATION_CMD="$MIGRATION_CMD --no-backup"
    fi
    
    if [[ "$FORCE" == true ]]; then
        MIGRATION_CMD="$MIGRATION_CMD --force"
    fi
    
    # Run migration with timeout
    timeout "$MIGRATION_TIMEOUT" $MIGRATION_CMD
    
    if [[ $? -eq 0 ]]; then
        log "Migration completed successfully"
        return 0
    else
        error "Migration failed"
    fi
}

rollback_migration() {
    log "Rolling back to revision $TARGET_REVISION..."
    
    # Confirm rollback in production
    if [[ "$FORCE" != true ]]; then
        echo -e "${YELLOW}WARNING: You are about to rollback the database in production!${NC}"
        echo "Target revision: $TARGET_REVISION"
        read -p "Type 'ROLLBACK' to confirm: " confirmation
        
        if [[ "$confirmation" != "ROLLBACK" ]]; then
            log "Rollback cancelled"
            exit 0
        fi
    fi
    
    ROLLBACK_CMD="python3 scripts/manage-migrations.py rollback --target $TARGET_REVISION"
    
    if [[ "$NO_BACKUP" == true ]]; then
        ROLLBACK_CMD="$ROLLBACK_CMD --no-backup"
    fi
    
    timeout "$MIGRATION_TIMEOUT" $ROLLBACK_CMD
    
    if [[ $? -eq 0 ]]; then
        log "Rollback completed successfully"
        return 0
    else
        error "Rollback failed"
    fi
}

list_backups() {
    log "Listing available backups..."
    python3 scripts/manage-migrations.py list-backups --limit 20
}

# Cleanup function
cleanup() {
    local exit_code=$?
    
    log "Performing cleanup..."
    
    # Disable maintenance mode on exit
    disable_maintenance_mode
    
    # If migration failed and we have a backup, suggest rollback
    if [[ $exit_code -ne 0 && -f /tmp/last_backup_name ]]; then
        BACKUP_NAME=$(cat /tmp/last_backup_name)
        warn "Migration failed! Backup available: $BACKUP_NAME"
        echo "To restore from backup, run:"
        echo "  python3 scripts/manage-migrations.py restore /path/to/backup"
    fi
    
    rm -f /tmp/last_backup_name
    exit $exit_code
}

# Set up signal handlers
trap cleanup EXIT INT TERM

# Pre-flight checks
log "Starting production migration process..."
log "Command: $COMMAND"
log "Target revision: $TARGET_REVISION"
log "Force mode: $FORCE"
log "Backup: $(if [[ "$NO_BACKUP" == true ]]; then echo "disabled"; else echo "enabled"; fi)"
log "Maintenance mode: $(if [[ "$MAINTENANCE_MODE" == true ]]; then echo "enabled"; else echo "disabled"; fi)"
log "Timeout: ${MIGRATION_TIMEOUT}s"

# Execute command
case $COMMAND in
    status)
        check_migration_status
        ;;
    validate)
        validate_migrations
        ;;
    backup)
        create_backup
        ;;
    dry-run)
        perform_dry_run
        ;;
    migrate)
        # Full migration process with safety checks
        log "Starting full migration process..."
        
        # Step 1: Validate
        validate_migrations || error "Validation failed"
        
        # Step 2: Dry run
        perform_dry_run || error "Dry run failed"
        
        # Step 3: Create backup
        create_backup || error "Backup failed"
        
        # Step 4: Enable maintenance mode
        enable_maintenance_mode
        
        # Step 5: Run migration
        run_migration || {
            disable_maintenance_mode
            error "Migration failed"
        }
        
        # Step 6: Disable maintenance mode
        disable_maintenance_mode
        
        log "Migration process completed successfully!"
        ;;
    rollback)
        # Rollback process
        log "Starting rollback process..."
        
        # Create backup before rollback
        if [[ "$NO_BACKUP" != true ]]; then
            create_backup || error "Pre-rollback backup failed"
        fi
        
        # Enable maintenance mode
        enable_maintenance_mode
        
        # Perform rollback
        rollback_migration || {
            disable_maintenance_mode
            error "Rollback failed"
        }
        
        # Disable maintenance mode
        disable_maintenance_mode
        
        log "Rollback process completed successfully!"
        ;;
    list-backups)
        list_backups
        ;;
    *)
        error "Unknown command: $COMMAND"
        ;;
esac

log "Production migration script completed successfully!"
