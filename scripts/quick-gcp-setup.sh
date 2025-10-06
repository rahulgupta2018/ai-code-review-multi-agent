#!/bin/bash

# Quick setup wrapper for Google Cloud project creation
# This script provides simplified commands for common operations

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MAIN_SCRIPT="${SCRIPT_DIR}/create-google-cloud-project.sh"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${BLUE}Google Cloud Project Quick Setup${NC}"
echo "=================================="
echo

case "${1:-help}" in
    "setup"|"create")
        echo -e "${GREEN}Creating Google Cloud project with default settings...${NC}"
        echo "Email: chilternwarriors.cc@gmail.com"
        echo
        exec "$MAIN_SCRIPT" create
        ;;
    "setup-custom"|"create-custom")
        echo -e "${GREEN}Creating Google Cloud project with custom email...${NC}"
        read -p "Enter your email: " email
        echo
        exec "$MAIN_SCRIPT" create -e "$email"
        ;;
    "test"|"dry-run")
        echo -e "${GREEN}Testing what would be created (dry run)...${NC}"
        echo
        exec "$MAIN_SCRIPT" create -d
        ;;
    "verify"|"check")
        echo -e "${GREEN}Verifying current setup...${NC}"
        echo
        exec "$MAIN_SCRIPT" verify
        ;;
    "list"|"projects")
        echo -e "${GREEN}Listing your Google Cloud projects...${NC}"
        echo
        exec "$MAIN_SCRIPT" list-projects
        ;;
    "config"|"configure")
        echo -e "${GREEN}Updating configuration...${NC}"
        echo
        exec "$MAIN_SCRIPT" update-config
        ;;
    "help"|*)
        echo "Quick commands:"
        echo
        echo -e "${YELLOW}Basic Operations:${NC}"
        echo "  $0 setup          - Create project with chilternwarriors.cc@gmail.com"
        echo "  $0 setup-custom   - Create project with your email"
        echo "  $0 test           - Dry run to see what would be created"
        echo "  $0 verify         - Check current setup"
        echo
        echo -e "${YELLOW}Management:${NC}"
        echo "  $0 list           - List your Google Cloud projects"
        echo "  $0 config         - Update configuration settings"
        echo
        echo -e "${YELLOW}Full Options:${NC}"
        echo "  Run: ${SCRIPT_DIR}/create-google-cloud-project.sh --help"
        echo
        ;;
esac