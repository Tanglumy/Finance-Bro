#!/usr/bin/env python3
"""
Test runner for Finance-Bro backend tests.
"""

import subprocess
import sys
import os
import argparse
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and return success status."""
    print(f"{'=' * 60}")
    print(f"Running: {description or ' '.join(cmd)}")
    print(f"{'=' * 60}")
    
    try:
        result = subprocess.run(cmd, check=True, capture_output=False)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Command failed with exit code {e.returncode}")
        return False
    except FileNotFoundError:
        print(f"Command not found: {cmd[0]}")
        return False

def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(description="Run Finance-Bro tests")
    parser.add_argument("--unit", action="store_true", help="Run unit tests only")
    parser.add_argument("--integration", action="store_true", help="Run integration tests only")
    parser.add_argument("--api", action="store_true", help="Run API tests only")
    parser.add_argument("--formula", action="store_true", help="Run formula engine tests only")
    parser.add_argument("--ts", action="store_true", help="Run time series tests only")
    parser.add_argument("--portfolio", action="store_true", help="Run portfolio tests only")
    parser.add_argument("--slow", action="store_true", help="Include slow tests")
    parser.add_argument("--network", action="store_true", help="Include network tests")
    parser.add_argument("--coverage", action="store_true", help="Generate coverage report")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--parallel", "-n", type=int, default=1, help="Run tests in parallel")
    parser.add_argument("--file", "-f", help="Run specific test file")
    parser.add_argument("--pattern", "-k", help="Run tests matching pattern")
    parser.add_argument("--html-report", action="store_true", help="Generate HTML coverage report")
    parser.add_argument("--xml-report", action="store_true", help="Generate XML coverage report")
    
    args = parser.parse_args()
    
    # Check if we're in the backend directory
    if not Path("pytest.ini").exists():
        print("Please run this script from the backend directory")
        sys.exit(1)
    
    # Build pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add verbosity
    if args.verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    # Add parallel execution
    if args.parallel > 1:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add coverage
    if args.coverage or args.html_report or args.xml_report:
        cmd.extend(["--cov=src", "--cov-report=term-missing"])
        
        if args.html_report:
            cmd.append("--cov-report=html")
            
        if args.xml_report:
            cmd.append("--cov-report=xml")
    
    # Add markers based on test type
    markers = []
    if args.unit:
        markers.append("unit")
    if args.integration:
        markers.append("integration")
    if args.api:
        markers.append("api")
    if args.formula:
        markers.append("formula")
    if args.ts:
        markers.append("ts")
    if args.portfolio:
        markers.append("portfolio")
    
    if markers:
        cmd.extend(["-m", " or ".join(markers)])
    
    # Exclude slow and network tests by default
    exclusions = []
    if not args.slow:
        exclusions.append("not slow")
    if not args.network:
        exclusions.append("not network")
    
    if exclusions:
        if markers:
            cmd.extend(["and", "(" + " and ".join(exclusions) + ")"])
        else:
            cmd.extend(["-m", " and ".join(exclusions)])
    
    # Add specific file
    if args.file:
        cmd.append(f"tests/{args.file}")
    
    # Add pattern matching
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    # Add default test path if no specific file
    if not args.file:
        cmd.append("tests/")
    
    # Run the tests
    print("Finance-Bro Test Runner")
    print("=" * 60)
    print(f"Python: {sys.executable}")
    print(f"Working directory: {os.getcwd()}")
    print(f"Test command: {' '.join(cmd)}")
    print()
    
    success = run_command(cmd, "Running tests")
    
    if success:
        print("\n" + "=" * 60)
        print("✅ All tests passed!")
        print("=" * 60)
        
        # Show coverage report location if generated
        if args.html_report:
            print(f"📊 HTML coverage report: {Path('htmlcov/index.html').absolute()}")
        if args.xml_report:
            print(f"📊 XML coverage report: {Path('coverage.xml').absolute()}")
            
    else:
        print("\n" + "=" * 60)
        print("❌ Some tests failed!")
        print("=" * 60)
        sys.exit(1)

if __name__ == "__main__":
    main()