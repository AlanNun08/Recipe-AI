#!/usr/bin/env python3
"""
Project Cleanup and Reorganization Script
Removes test files, duplicates, and organizes the codebase
"""

import os
import shutil
from pathlib import Path

def cleanup_project():
    """Main cleanup function"""
    base_path = Path("/app")
    
    # Files and directories to remove
    cleanup_items = [
        # Test files
        "test_recipe_system.py",
        "dietary_filtering_test.py", 
        "test_integration.py",
        "detailed_preference_test.py",
        "enhanced_weekly_recipe_test.py",
        "test_data_integrity.py",
        "backend_test.py",
        "test_performance.py",
        "run_all_tests.py",
        "test_api_endpoints.py",
        "backend_test_results.txt",
        "production_test.log",
        "test-fixed.log",
        "test-production.log",
        "main_app.log",
        "production_analysis_results.json",
        
        # Test configuration files
        "playwright.config.js",
        "jest.config.js",
        "pytest.ini",
        
        # Test directories
        "tests/",
        
        # Build and deployment scripts (keep only essential ones)
        "test-build.sh",
        "secure-deploy.sh",
        "verify_env_vars.py",
        "verify_production.sh",
        "build_for_deployment.sh",
        "add-secret-values.sh",
        "setup-secrets.sh",
        
        # Debug and development files
        "env_debug.py",
        "backend_env_check.py",
        "login_debug.py",
        "stripe_env_test.py",
        "db_investigation.py",
        
        # Backup files
        "backup/",
        "backend/server.py.backup",
        "backend/server.py.backup_before_v2_replacement",
        "backend/=5.0.0",
        
        # Cleanup scripts and fixes
        "deploy_cleanup.sh",
        "production_account_cleanup.py",
        "production_api_analysis.py",
        "execute_fix_now.py",
        "production_account_fix_immediate.py",
        "deploy_account_fix.sh",
        "production_cleanup.py",
        "production_database_cleanup.py",
        "direct_account_fix.py",
        "expire_user_trial.py",
        "fix_demo_user.py",
        "walmart_integration_v2.py",
        
        # Build artifacts
        "buildyoursmartcart-deployment.tar.gz",
        "0",
        
        # Temporary files
        "backend/temp_function.py",
        
        # Duplicate documentation (keep essential ones)
        "DEPLOYMENT_TROUBLESHOOTING.md",
        "CACHE_BUSTING_GUIDE.md",
        "BUILD_OPTIMIZATION.md",
        "PRODUCTION_CLEANUP_SOLUTION.md",
        "ACCOUNT_FIX_SUMMARY.md",
        "DOUBLE_API_PREFIX_FIX.md",
        
        # GitHub workflows directory (since we're not using GitHub)
        ".github/",
        
        # Node modules backup if any
        "node_modules",
        "yarn.lock",
    ]
    
    print("🧹 Starting project cleanup...")
    
    removed_count = 0
    for item in cleanup_items:
        item_path = base_path / item
        if item_path.exists():
            try:
                if item_path.is_dir():
                    shutil.rmtree(item_path)
                    print(f"📁 Removed directory: {item}")
                else:
                    item_path.unlink()
                    print(f"📄 Removed file: {item}")
                removed_count += 1
            except Exception as e:
                print(f"⚠️  Could not remove {item}: {e}")
    
    print(f"\n✅ Cleanup complete! Removed {removed_count} items.")
    return removed_count

if __name__ == "__main__":
    cleanup_project()