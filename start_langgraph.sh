#!/bin/bash
# Start LangGraph Dev Server
# This script is designed to be run by launchd at login

# Configuration
PROJECT_DIR="/Users/stephane/Documents/work/chat-langchain"
LOG_FILE="/tmp/langgraph_dev.log"
PID_FILE="/tmp/langgraph_dev.pid"
MAX_RETRIES=10
RETRY_DELAY=2

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Function to check if network is available
wait_for_network() {
    local retries=0
    log "Waiting for network connectivity..."

    while [ $retries -lt $MAX_RETRIES ]; do
        if ping -c 1 8.8.8.8 >/dev/null 2>&1; then
            log "Network is available"
            return 0
        fi
        retries=$((retries + 1))
        log "Network not ready, retry $retries/$MAX_RETRIES"
        sleep $RETRY_DELAY
    done

    log "WARNING: Network check failed after $MAX_RETRIES retries, continuing anyway..."
    return 1
}

# Function to check if port 2024 is available
check_port() {
    if lsof -Pi :2024 -sTCP:LISTEN -t >/dev/null 2>&1; then
        log "ERROR: Port 2024 is already in use"
        lsof -Pi :2024 -sTCP:LISTEN | tee -a "$LOG_FILE"
        return 1
    fi
    log "Port 2024 is available"
    return 0
}

# Function to find poetry virtualenv
find_poetry_venv() {
    cd "$PROJECT_DIR" || exit 1
    local venv_path
    venv_path=$(poetry env info --path 2>/dev/null)

    if [ -z "$venv_path" ] || [ ! -d "$venv_path" ]; then
        log "ERROR: Poetry virtualenv not found"
        return 1
    fi

    echo "$venv_path"
    return 0
}

# Main execution
main() {
    log "========================================="
    log "Starting LangGraph Dev Server"
    log "========================================="

    # Wait for network
    wait_for_network

    # Additional delay to ensure system is fully ready
    sleep 5

    # Check if already running
    if [ -f "$PID_FILE" ]; then
        OLD_PID=$(cat "$PID_FILE")
        if ps -p "$OLD_PID" > /dev/null 2>&1; then
            log "LangGraph dev is already running (PID: $OLD_PID)"
            exit 0
        else
            log "Removing stale PID file"
            rm -f "$PID_FILE"
        fi
    fi

    # Check port availability
    if ! check_port; then
        log "ERROR: Cannot start, port 2024 is in use"
        exit 1
    fi

    # Change to project directory
    cd "$PROJECT_DIR" || {
        log "ERROR: Cannot change to project directory: $PROJECT_DIR"
        exit 1
    }

    # Find poetry virtualenv
    VENV_PATH=$(find_poetry_venv)
    if [ -z "$VENV_PATH" ]; then
        log "ERROR: Failed to find poetry virtualenv"
        exit 1
    fi

    log "Using virtualenv: $VENV_PATH"

    # Start langgraph dev in background
    log "Starting langgraph dev on port 2024..."

    # Use poetry run to ensure correct environment
    nohup poetry run langgraph dev --no-browser --port 2024 >> "$LOG_FILE" 2>&1 &

    # Save PID
    LANGGRAPH_PID=$!
    echo "$LANGGRAPH_PID" > "$PID_FILE"

    log "LangGraph dev started with PID: $LANGGRAPH_PID"

    # Wait a bit and verify it's running
    sleep 3

    if ps -p "$LANGGRAPH_PID" > /dev/null 2>&1; then
        log "✅ LangGraph dev is running successfully"
        log "Logs: $LOG_FILE"
        log "PID: $LANGGRAPH_PID"
        exit 0
    else
        log "❌ ERROR: LangGraph dev failed to start"
        log "Check logs at: $LOG_FILE"
        rm -f "$PID_FILE"
        exit 1
    fi
}

# Run main function
main "$@"
