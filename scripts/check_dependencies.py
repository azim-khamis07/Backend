#!/usr/bin/env python3
"""
Dependency management script for expense-tracker-backend.

This script checks for outdated dependencies and provides a plan for updates.
"""

import json
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Tuple


def run_command(cmd: List[str]) -> Tuple[str, int]:
    """Run a command and return output and exit code."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, check=False
        )
        return result.stdout.strip(), result.returncode
    except Exception as e:
        return str(e), 1


def check_pip_outdated() -> Dict[str, str]:
    """Check for outdated packages using pip list --outdated."""
    print("Checking for outdated packages...")
    output, exit_code = run_command(
        [sys.executable, "-m", "pip", "list", "--outdated", "--format=json"]
    )
    
    if exit_code != 0:
        print(f"Warning: pip list --outdated failed: {output}")
        return {}
    
    try:
        packages = json.loads(output)
        return {pkg["name"]: pkg.get("latest_version", "unknown") 
                for pkg in packages}
    except json.JSONDecodeError:
        print(f"Warning: Failed to parse pip output: {output}")
        return {}


def check_pipdeptree() -> Dict[str, List[str]]:
    """Get dependency tree using pipdeptree."""
    output, exit_code = run_command(
        [sys.executable, "-m", "pip", "show", "pipdeptree"]
    )
    
    if exit_code != 0:
        print("Installing pipdeptree for dependency tree analysis...")
        run_command([sys.executable, "-m", "pip", "install", "pipdeptree", "-q"])
    
    output, _ = run_command(
        [sys.executable, "-m", "pipdeptree", "--json"]
    )
    
    try:
        return json.loads(output)
    except json.JSONDecodeError:
        return {}


def check_safety_vulnerabilities() -> None:
    """Check for known security vulnerabilities using safety."""
    print("\nChecking for security vulnerabilities...")
    output, exit_code = run_command(
        [sys.executable, "-m", "pip", "show", "safety"]
    )
    
    if exit_code != 0:
        print("Installing safety for security checks...")
        run_command([sys.executable, "-m", "pip", "install", "safety", "-q"])
    
    output, exit_code = run_command(
        [sys.executable, "-m", "safety", "check", "--json"]
    )
    
    if exit_code == 0 and output:
        try:
            vulnerabilities = json.loads(output)
            if vulnerabilities:
                print("\n⚠️  Security vulnerabilities found:")
                for vuln in vulnerabilities:
                    print(f"  - {vuln.get('package', 'unknown')}: {vuln.get('vulnerability', 'unknown')}")
            else:
                print("✓ No known security vulnerabilities found")
        except json.JSONDecodeError:
            pass
    else:
        print("⚠️  Could not check for vulnerabilities (safety DB might need update)")


def read_project_dependencies() -> Dict[str, str]:
    """Read dependencies from pyproject.toml."""
    import tomllib
    
    pyproject_path = Path("pyproject.toml")
    if not pyproject_path.exists():
        return {}
    
    with open(pyproject_path, "rb") as f:
        data = tomllib.load(f)
    
    deps = {}
    project = data.get("project", {})
    
    # Main dependencies
    for dep in project.get("dependencies", []):
        if "==" in dep:
            name, version = dep.split("==", 1)
            deps[name.strip()] = version.strip()
    
    # Optional dependencies
    optional = project.get("optional-dependencies", {})
    for group in optional.values():
        for dep in group:
            if "==" in dep:
                name, version = dep.split("==", 1)
                deps[name.strip()] = version.strip()
    
    return deps


def generate_update_plan(outdated: Dict[str, str], 
                        project_deps: Dict[str, str]) -> None:
    """Generate a plan for updating dependencies."""
    print("\n" + "="*70)
    print("DEPENDENCY UPDATE PLAN")
    print("="*70)
    
    if not outdated:
        print("\n✓ All dependencies are up to date!")
        return
    
    print(f"\nFound {len(outdated)} outdated package(s):\n")
    
    # Group by major/minor/patch updates
    major_updates = []
    minor_updates = []
    patch_updates = []
    
    for pkg_name, latest_version in outdated.items():
        if pkg_name not in project_deps:
            continue
            
        current_version = project_deps[pkg_name]
        current_parts = current_version.split(".")
        latest_parts = latest_version.split(".")
        
        if len(current_parts) > 0 and len(latest_parts) > 0:
            if current_parts[0] != latest_parts[0]:
                major_updates.append((pkg_name, current_version, latest_version))
            elif len(current_parts) > 1 and len(latest_parts) > 1:
                if current_parts[1] != latest_parts[1]:
                    minor_updates.append((pkg_name, current_version, latest_version))
                elif len(current_parts) > 2 and len(latest_parts) > 2:
                    if current_parts[2] != latest_parts[2]:
                        patch_updates.append((pkg_name, current_version, latest_version))
    
    if major_updates:
        print("🔴 MAJOR UPDATES (Breaking changes possible):")
        for pkg, current, latest in major_updates:
            print(f"  {pkg}: {current} → {latest}")
        print()
    
    if minor_updates:
        print("🟡 MINOR UPDATES (New features, backward compatible):")
        for pkg, current, latest in minor_updates:
            print(f"  {pkg}: {current} → {latest}")
        print()
    
    if patch_updates:
        print("🟢 PATCH UPDATES (Bug fixes only):")
        for pkg, current, latest in patch_updates:
            print(f"  {pkg}: {current} → {latest}")
        print()
    
    print("\nRecommended update steps:")
    print("1. Review breaking changes for major updates")
    print("2. Update pyproject.toml with new versions")
    print("3. Run: pip install --upgrade -e '.[dev]'")
    print("4. Run tests: pytest")
    print("5. Check for deprecation warnings")


def main():
    """Main function."""
    print("="*70)
    print("DEPENDENCY CHECKER")
    print("="*70)
    
    # Read project dependencies
    project_deps = read_project_dependencies()
    print(f"\nFound {len(project_deps)} dependencies in pyproject.toml")
    
    # Check for outdated packages
    outdated = check_pip_outdated()
    
    # Check for security vulnerabilities
    check_safety_vulnerabilities()
    
    # Generate update plan
    generate_update_plan(outdated, project_deps)
    
    print("\n" + "="*70)
    print("To check dependencies manually:")
    print("  pip list --outdated")
    print("  pipdeptree")
    print("  safety check")
    print("="*70)


if __name__ == "__main__":
    main()

