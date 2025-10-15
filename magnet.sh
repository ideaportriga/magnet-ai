#!/bin/bash

# Magnet AI Docker Compose Management Script

set -e

# Docker Compose file
COMPOSE_FILE="docker-compose-monolith.yml"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

print_header() {
    echo -e "${BLUE}[MAGNET AI]${NC} $1"
}

# Function to check if .env files exist
check_env_files() {
    if [ ! -f .env ]; then
        print_warning ".env file not found. Creating from .env.docker.example..."
        cp .env.docker.example .env
        print_status ".env file created from template"
        print_warning "Please review and configure .env before continuing"
        exit 1
    fi
}

# Function to setup for first run
first_run_setup() {
    print_header "Setting up for first run with database initialization"
    
    check_env_files
    
    # Enable first-time database initialization and fixtures
    sed -i.bak 's/INIT_DB=false/INIT_DB=true/' .env
    sed -i.bak 's/RUN_FIXTURES=false/RUN_FIXTURES=true/' .env
    sed -i.bak 's/RUN_MIGRATIONS=true/RUN_MIGRATIONS=false/' .env
    sed -i.bak 's/RESET_DB=true/RESET_DB=false/' .env
    
    print_status "Enabled first-time database initialization and fixtures loading"
    print_status "Starting services..."
    
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_status "Services started! Waiting for initialization to complete..."
    sleep 15
    
    # Show logs to see initialization progress
    docker-compose -f "$COMPOSE_FILE" logs app
    
    print_status "First run setup complete!"
    print_status "API: http://localhost:5000"
    print_status "API Docs: http://localhost:5000/docs"
    print_warning "IMPORTANT: Set INIT_DB=false in .env for next runs"
}

# Function for normal startup
normal_startup() {
    print_header "Starting services (normal mode)"
    
    check_env_files
    
    # Disable all database initialization options for normal run
    sed -i.bak 's/INIT_DB=true/INIT_DB=false/' .env
    sed -i.bak 's/RUN_MIGRATIONS=true/RUN_MIGRATIONS=false/' .env
    sed -i.bak 's/RUN_FIXTURES=true/RUN_FIXTURES=false/' .env
    sed -i.bak 's/RESET_DB=true/RESET_DB=false/' .env
    
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_status "Services started!"
    print_status "API: http://localhost:5000"
    print_status "API Docs: http://localhost:5000/docs"
}

# Function to stop services
stop_services() {
    print_header "Stopping all services"
    docker-compose -f "$COMPOSE_FILE" down
    print_status "Services stopped"
}

# Function to show logs
show_logs() {
    service=${2:-""}
    if [ -n "$service" ]; then
        print_header "Showing logs for $service"
        docker-compose -f "$COMPOSE_FILE" logs -f "$service"
    else
        print_header "Showing logs for all services"
        docker-compose -f "$COMPOSE_FILE" logs -f
    fi
}

# Function to run migrations manually
run_migrations() {
    print_header "Running database migrations"
    docker-compose -f "$COMPOSE_FILE" exec app sh -c "PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini upgrade head"
    print_status "Migrations completed"
}

# Function to load fixtures manually  
load_fixtures() {
    print_header "Loading database fixtures"
    docker-compose -f "$COMPOSE_FILE" exec app sh -c "PYTHONPATH=/app/src .venv/bin/python /app/manage_fixtures.py fixtures load"
    print_status "Fixtures loaded"
}

# Function to create a new migration
create_migration() {
    migration_message=$2
    if [ -z "$migration_message" ]; then
        print_error "Please specify migration message: ./magnet.sh create-migration \"message\""
        exit 1
    fi
    
    print_header "Creating new migration: $migration_message"
    docker-compose -f "$COMPOSE_FILE" exec app sh -c "PYTHONPATH=/app/src .venv/bin/alembic -c /app/src/core/db/migrations/alembic.ini revision --autogenerate -m \"$migration_message\""
    print_status "Migration created: $migration_message"
}

# Function to reset database (DESTRUCTIVE!)
reset_database() {
    print_warning "This will COMPLETELY RESET the database and all migrations!"
    print_warning "ALL DATA WILL BE LOST!"
    echo -n "Type 'RESET' to confirm: "
    read -r confirmation
    if [ "$confirmation" != "RESET" ]; then
        print_status "Reset cancelled"
        return
    fi
    
    print_header "Resetting database completely"
    
    # Stop services first
    docker-compose -f "$COMPOSE_FILE" down
    
    # Enable reset mode
    sed -i.bak 's/INIT_DB=true/INIT_DB=false/' .env
    sed -i.bak 's/RUN_MIGRATIONS=true/RUN_MIGRATIONS=false/' .env
    sed -i.bak 's/RUN_FIXTURES=false/RUN_FIXTURES=true/' .env
    sed -i.bak 's/RESET_DB=false/RESET_DB=true/' .env
    
    # Start services with reset
    docker-compose -f "$COMPOSE_FILE" up -d
    
    print_status "Database reset complete!"
}

# Function to update database schema
update_schema() {
    print_header "Updating database schema (applying migrations)"
    
    check_env_files
    
    # Enable migrations only
    sed -i.bak 's/INIT_DB=true/INIT_DB=false/' .env
    sed -i.bak 's/RUN_MIGRATIONS=false/RUN_MIGRATIONS=true/' .env
    sed -i.bak 's/RUN_FIXTURES=true/RUN_FIXTURES=false/' .env
    sed -i.bak 's/RESET_DB=true/RESET_DB=false/' .env
    
    # Restart API service to apply migrations
    docker-compose -f "$COMPOSE_FILE" restart app
    
    # Show logs
    sleep 5
    docker-compose -f "$COMPOSE_FILE" logs app
    
    print_status "Schema update complete!"
}

# Function to access database
db_access() {
    print_header "Accessing PostgreSQL database"
    docker-compose -f "$COMPOSE_FILE" exec postgres psql -U postgres -d magnet_dev
}

# Function to backup database
backup_db() {
    backup_file="backup_$(date +%Y%m%d_%H%M%S).sql"
    print_header "Creating database backup: $backup_file"
    docker-compose -f "$COMPOSE_FILE" exec postgres pg_dump -U postgres magnet_dev > "$backup_file"
    print_status "Backup created: $backup_file"
}

# Function to restore database
restore_db() {
    backup_file=$2
    if [ -z "$backup_file" ]; then
        print_error "Please specify backup file: ./magnet.sh restore <backup_file>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        print_error "Backup file not found: $backup_file"
        exit 1
    fi
    
    print_header "Restoring database from: $backup_file"
    docker-compose -f "$COMPOSE_FILE" exec -T postgres psql -U postgres magnet_dev < "$backup_file"
    print_status "Database restored from $backup_file"
}

# Function to clean everything
clean_all() {
    print_warning "This will remove all containers, volumes, and images. Data will be lost!"
    echo -n "Are you sure? (y/N): "
    read -r response
    if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
        print_header "Cleaning up all Docker resources"
        docker-compose -f "$COMPOSE_FILE" down -v
        docker-compose -f "$COMPOSE_FILE" rm -f
        docker system prune -f
        print_status "Cleanup completed"
    else
        print_status "Cleanup cancelled"
    fi
}

# Function to rebuild services
rebuild() {
    service=${2:-""}
    if [ -n "$service" ]; then
        print_header "Rebuilding service: $service"
        docker-compose -f "$COMPOSE_FILE" build "$service"
    else
        print_header "Rebuilding all services"
        docker-compose -f "$COMPOSE_FILE" build
    fi
    print_status "Rebuild completed"
}

# Function to show service status
status() {
    print_header "Service Status"
    docker-compose -f "$COMPOSE_FILE" ps
    echo ""
    print_header "Service Health"
    docker-compose -f "$COMPOSE_FILE" exec postgres pg_isready -U postgres -d magnet_dev || print_error "PostgreSQL not ready"
    echo ""
    print_header "Resource Usage"
    docker stats --no-stream magnet-app magnet-postgres 2>/dev/null || print_warning "Containers not running"
}

# Help function
show_help() {
    cat << EOF
Magnet AI Docker Compose Management Script

Usage: ./magnet.sh <command> [options]

🚀 Startup Commands:
    first-run           Initial setup with database creation and sample data
    start              Start services in normal mode (no DB changes)
    stop               Stop all services
    restart            Restart all services

📊 Database Management:
    migrate            Apply pending database migrations
    fixtures           Load database fixtures/sample data  
    create-migration   Create new migration (usage: create-migration "message")
    update-schema      Apply migrations to update database schema
    reset-db           DESTRUCTIVE: Completely reset database and migrations
    db                 Access PostgreSQL database shell
    backup             Create database backup
    restore <file>     Restore database from backup file

🔧 Service Management:
    logs [service]     Show logs for all services or specific service
    status             Show service status and health
    rebuild [service]  Rebuild Docker images for all or specific service
    clean              Clean up all containers, volumes, and images (DESTRUCTIVE!)

❓ Help:
    help               Show this help message

Services:
    postgres           PostgreSQL database with pgvector extension
    app                Monolith application (API + Web frontend)

Examples:
    ./magnet.sh first-run                    # Complete initial setup
    ./magnet.sh start                        # Normal startup
    ./magnet.sh create-migration "add users" # Create new migration
    ./magnet.sh update-schema                # Apply pending migrations
    ./magnet.sh logs api                     # Show API logs only
    ./magnet.sh backup                       # Create database backup
    ./magnet.sh restore backup.sql           # Restore from backup

Database Initialization Modes:
    - first-run: Creates initial schema + loads sample data (new installations)
    - update-schema: Applies migrations only (existing installations)  
    - reset-db: Complete reset (DESTRUCTIVE - removes all data!)

EOF
}

# Main script logic
case "${1}" in
    "first-run")
        first_run_setup
        ;;
    "start")
        normal_startup
        ;;
    "stop")
        stop_services
        ;;
    "restart")
        stop_services
        sleep 2
        normal_startup
        ;;
    "logs")
        show_logs "$@"
        ;;
    "migrate")
        run_migrations
        ;;
    "fixtures")
        load_fixtures
        ;;
    "create-migration")
        create_migration "$@"
        ;;
    "update-schema")
        update_schema
        ;;
    "reset-db")
        reset_database
        ;;
    "db")
        db_access
        ;;
    "backup")
        backup_db
        ;;
    "restore")
        restore_db "$@"
        ;;
    "status")
        status
        ;;
    "rebuild")
        rebuild "$@"
        ;;
    "clean")
        clean_all
        ;;
    "help"|"--help"|"-h")
        show_help
        ;;
    *)
        print_error "Unknown command: $1"
        echo ""
        show_help
        exit 1
        ;;
esac