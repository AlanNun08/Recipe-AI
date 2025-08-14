#!/usr/bin/env python3
"""
Security Validation Script
Ensures no hardcoded API keys exist in the codebase
"""

import os
import re
import sys
from pathlib import Path

# Patterns for potentially sensitive keys
SENSITIVE_PATTERNS = {
    'stripe_live': r'sk_live_[A-Za-z0-9]{24,}',
    'stripe_test': r'sk_test_[A-Za-z0-9]{24,}',
    'stripe_pub_live': r'pk_live_[A-Za-z0-9]{24,}',
    'stripe_pub_test': r'pk_test_[A-Za-z0-9]{24,}',
    'openai': r'sk-[A-Za-z0-9]{32,}',
    'private_key': r'-----BEGIN PRIVATE KEY-----\s*[A-Za-z0-9+/\s]{100,}\s*-----END PRIVATE KEY-----',
}

# Files to exclude from scanning
EXCLUDE_PATTERNS = [
    '.git',
    'node_modules',
    '__pycache__',
    '.env.example',
    'validate_security.py',  # This file itself
    'SECURITY_AND_DEPLOYMENT.md',  # Contains examples
    'GOOGLE_CLOUD_ENVIRONMENT_VARIABLES.md',  # Contains examples
]

# Allowed placeholder patterns (these are OK)
PLACEHOLDER_PATTERNS = [
    'your-stripe-secret-key-here',
    'your-stripe-publishable-key-here',
    'sk_live_your-stripe-secret-key-here',
    'pk_live_your-stripe-publishable-key-here',
    'sk_live_...',
    'pk_live_...',
    'your-openai-key-here',
    'your-walmart-private-key-here',
    'your-actual-stripe-secret-key-here',
    'your-actual-stripe-publishable-key-here',
]

def should_exclude(file_path):
    """Check if file should be excluded from scanning"""
    for pattern in EXCLUDE_PATTERNS:
        if pattern in str(file_path):
            return True
    return False

def is_placeholder(match_text):
    """Check if the matched text is a placeholder"""
    for placeholder in PLACEHOLDER_PATTERNS:
        if placeholder in match_text:
            return True
    return False

def scan_file(file_path):
    """Scan a single file for sensitive patterns"""
    violations = []
    
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        for pattern_name, pattern in SENSITIVE_PATTERNS.items():
            matches = re.finditer(pattern, content, re.MULTILINE | re.DOTALL)
            
            for match in matches:
                # Check if this is a placeholder
                if not is_placeholder(match.group()):
                    line_num = content[:match.start()].count('\n') + 1
                    violations.append({
                        'file': file_path,
                        'line': line_num,
                        'pattern': pattern_name,
                        'match': match.group()[:50] + '...' if len(match.group()) > 50 else match.group()
                    })
                    
    except Exception as e:
        print(f"Warning: Could not scan {file_path}: {e}")
        
    return violations

def main():
    """Main security validation function"""
    print("🔒 Running Security Validation...")
    print("=" * 50)
    
    violations = []
    scanned_files = 0
    
    # Scan all relevant files
    for root, dirs, files in os.walk('.'):
        # Skip excluded directories
        dirs[:] = [d for d in dirs if not any(exclude in d for exclude in EXCLUDE_PATTERNS)]
        
        for file in files:
            file_path = Path(root) / file
            
            # Only scan text files
            if file_path.suffix in ['.py', '.js', '.jsx', '.ts', '.tsx', '.md', '.env', '.json', '.yaml', '.yml']:
                if not should_exclude(file_path):
                    file_violations = scan_file(file_path)
                    violations.extend(file_violations)
                    scanned_files += 1
    
    print(f"📁 Scanned {scanned_files} files")
    print()
    
    if violations:
        print("🚨 SECURITY VIOLATIONS FOUND:")
        print("=" * 50)
        
        for violation in violations:
            print(f"❌ {violation['file']}:{violation['line']}")
            print(f"   Pattern: {violation['pattern']}")
            print(f"   Match: {violation['match']}")
            print()
            
        print(f"Total violations: {len(violations)}")
        print("\n⚠️  Please remove hardcoded API keys and use environment variables!")
        return 1
    else:
        print("✅ SECURITY VALIDATION PASSED")
        print("   No hardcoded API keys found in codebase")
        print("   All sensitive data properly externalized to environment variables")
        return 0

if __name__ == "__main__":
    sys.exit(main())