#!/usr/bin/env python3
"""Script to identify and fix missing model imports in __init__.py"""

import os
import re
from pathlib import Path

def find_model_classes(models_dir):
    """Find all model classes in the models directory"""
    classes = {}
    
    for py_file in Path(models_dir).glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Find class definitions
            class_matches = re.findall(r'^class\s+([A-Z][A-Za-z0-9_]*)\s*\(', content, re.MULTILINE)
            for class_name in class_matches:
                classes[class_name] = py_file.stem
                
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
            
    return classes

def get_imported_classes(init_file):
    """Get currently imported classes from __init__.py"""
    imported = set()
    
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find import statements
        import_matches = re.findall(r'from\s+app\.models\.[a-z_]+\s+import\s+([A-Z][A-Za-z0-9_, ]+)', content)
        for match in import_matches:
            # Split by comma and clean up
            classes = [cls.strip() for cls in match.split(',')]
            imported.update(classes)
            
    except Exception as e:
        print(f"Error reading {init_file}: {e}")
        
    return imported

def main():
    models_dir = "app/models"
    init_file = "app/models/__init__.py"
    
    all_classes = find_model_classes(models_dir)
    imported_classes = get_imported_classes(init_file)
    
    print("All model classes found:")
    for class_name, module in sorted(all_classes.items()):
        print(f"  {class_name} (from {module})")
        
    print(f"\nCurrently imported: {len(imported_classes)} classes")
    print(f"Total classes found: {len(all_classes)} classes")
    
    missing = set(all_classes.keys()) - imported_classes
    if missing:
        print(f"\nMissing imports ({len(missing)}):")
        for class_name in sorted(missing):
            module = all_classes[class_name]
            print(f"  {class_name} (from {module})")
            print(f"    Add: from app.models.{module} import {class_name}")
    else:
        print("\nAll classes are imported!")

if __name__ == "__main__":
    main()