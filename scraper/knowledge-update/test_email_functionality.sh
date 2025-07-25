#!/bin/bash

# Test TD SYNNEX Email Reading Functionality
# Quick test script to verify email attachment reading works

echo "🧪 Testing TD SYNNEX Email Reading Functionality..."

# Check if we're in the correct directory
if [ ! -f "test_tdsynnex_attachments.py" ]; then
    echo "❌ Error: test script not found. Please run from knowledge-update directory."
    exit 1
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "❌ Error: .env file not found. Please create .env with required credentials."
    exit 1
fi

echo "📧 Testing email connection and TD SYNNEX attachment reading..."
python3 test_tdsynnex_attachments.py

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Email functionality test PASSED!"
    echo "📁 Check for 'hexalinks_701601-*.txt' file in current directory"
    echo ""
    echo "🚀 You can now run: ./start_knowledge_update_service.sh"
else
    echo ""
    echo "❌ Email functionality test FAILED!"
    echo "   Please check your Azure AD credentials in .env file"
fi