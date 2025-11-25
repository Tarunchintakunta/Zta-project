#!/bin/bash
# Quick test script to verify all improvements

echo "=========================================="
echo "Testing ZTA Project Improvements"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "TEST_IMPROVEMENTS.py" ]; then
    echo "Error: Please run this script from the zta_project directory"
    exit 1
fi

# Check Python
echo "1. Checking Python..."
python3 --version || { echo "Error: Python 3 not found"; exit 1; }
echo "   ✓ Python found"
echo ""

# Check dependencies
echo "2. Checking dependencies..."
python3 -c "import sklearn; print(f'   ✓ scikit-learn {sklearn.__version__}')" 2>/dev/null || {
    echo "   ⚠ scikit-learn not found. Installing..."
    pip install scikit-learn
}
python3 -c "import numpy; print(f'   ✓ numpy {numpy.__version__}')" 2>/dev/null || { echo "   ✗ numpy not found"; exit 1; }
python3 -c "import pandas; print(f'   ✓ pandas {pandas.__version__}')" 2>/dev/null || { echo "   ✗ pandas not found"; exit 1; }
echo ""

# Run tests
echo "3. Running comprehensive tests..."
echo "=========================================="
python3 TEST_IMPROVEMENTS.py

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "✓ All tests passed!"
    echo "=========================================="
    echo ""
    echo "Next steps:"
    echo "  - Run full experiment: python3 run_experiment.py"
    echo "  - Check HOW_TO_RUN.md for detailed instructions"
    exit 0
else
    echo ""
    echo "=========================================="
    echo "✗ Some tests failed"
    echo "=========================================="
    echo ""
    echo "Check the output above for details"
    exit 1
fi

