#!/bin/bash
# Quick test script for the upload

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FILE_PATH="~/Downloads/ec-synnex-701601-0708-0927.xls"

echo "Testing upload with file: $FILE_PATH"
echo ""

if [ -f "$(eval echo $FILE_PATH)" ]; then
    python3 "$SCRIPT_DIR/upload-to-copilot.py" "$FILE_PATH"
else
    echo "ERROR: File not found: $FILE_PATH"
    echo "Please check the file path in config.json or provide the correct path"
    echo ""
    echo "Usage: $0 [file_path]"
    echo "Example: $0 ~/Downloads/my-file.xls"
    
    if [ -n "$1" ]; then
        python3 "$SCRIPT_DIR/upload-to-copilot.py" "$1"
    fi
fi
