#!/usr/bin/env python3
"""Fix missing imports in __init__.py by adding critical models only"""

import re
from pathlib import Path

# Critical models that are commonly referenced in tests
CRITICAL_MODELS = {
    # Base models that many things inherit from
    'AuditableModel', 'BaseModel', 'SoftDeletableModel',
    
    # Core business models  
    'Product', 'InventoryItem', 'StockMovement', 'MovementType', 'InventoryStatus',
    'SalesOrder', 'SalesOrderItem', 'OrderStatus', 'PaymentMethod', 'PaymentStatus',
    'User', 'UserOrganization', 'UserRole', 'UserSession', 'UserActivityLog',
    'Organization', 'OrganizationInvitation', 'UserTransferRequest', 'Department',
    'Role', 'RolePermission', 'Permission', 'PermissionDependency',
    'Task', 'TaskDependency', 'TaskHistory', 'TaskPriority', 'TaskStatus', 'DependencyType',
    'Project', 'ProjectMember', 'ProjectMilestone',
    'Application', 'ApplicationApproval', 'Workflow', 'WorkflowInstance', 'WorkflowNode', 'WorkflowConnection', 'WorkflowTask',
    'PasswordHistory', 'UserPreferences', 'UserPrivacySettings',
    
    # Financial models
    'Expense', 'ExpenseApprovalFlow', 'ExpenseCategory', 'ExpenseStatus',
    'Budget', 'BudgetItem',
    
    # CRM models
    'Customer', 'CustomerContact', 'CustomerActivity', 'Opportunity',
    
    # Analytics and reporting
    'Report', 'ReportExecution', 'ReportWidget', 'Dashboard', 'DashboardWidget', 'Chart', 'DataSource',
    
    # Audit and security
    'AuditLog', 'CrossTenantPermissionRule', 'CrossTenantAuditLog',
}

def find_missing_models():
    """Find models that exist but are not imported"""
    models_dir = Path("app/models")
    init_file = models_dir / "__init__.py"
    
    # Get all model classes
    all_classes = {}
    for py_file in models_dir.glob("*.py"):
        if py_file.name == "__init__.py":
            continue
            
        try:
            with open(py_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            class_matches = re.findall(r'^class\s+([A-Z][A-Za-z0-9_]*)\s*\(', content, re.MULTILINE)
            for class_name in class_matches:
                all_classes[class_name] = py_file.stem
                
        except Exception as e:
            print(f"Error reading {py_file}: {e}")
    
    # Get imported classes
    imported = set()
    try:
        with open(init_file, 'r', encoding='utf-8') as f:
            content = f.read()
            
        import_matches = re.findall(r'from\s+app\.models\.[a-z_]+\s+import\s+([A-Z][A-Za-z0-9_, ]+)', content)
        for match in import_matches:
            classes = [cls.strip() for cls in match.split(',')]
            imported.update(classes)
            
    except Exception as e:
        print(f"Error reading {init_file}: {e}")
        return {}
    
    # Find critical missing models
    missing_critical = {}
    for class_name in CRITICAL_MODELS:
        if class_name not in imported and class_name in all_classes:
            missing_critical[class_name] = all_classes[class_name]
    
    return missing_critical

def add_missing_imports():
    """Add missing critical imports to __init__.py"""
    missing = find_missing_models()
    
    if not missing:
        print("All critical models are already imported!")
        return
    
    print(f"Adding {len(missing)} critical missing imports...")
    
    # Group by module
    by_module = {}
    for class_name, module in missing.items():
        if module not in by_module:
            by_module[module] = []
        by_module[module].append(class_name)
    
    # Read current __init__.py
    init_file = Path("app/models/__init__.py")
    with open(init_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Add imports at the end, before any __all__ definition
    new_imports = []
    for module, classes in sorted(by_module.items()):
        classes.sort()
        classes_str = ", ".join(classes)
        new_imports.append(f"from app.models.{module} import {classes_str}")
    
    # Add new imports
    import_section = "\n".join(new_imports)
    content += f"\n\n# Additional critical model imports\n{import_section}\n"
    
    # Write back
    with open(init_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("Added imports:")
    for imp in new_imports:
        print(f"  {imp}")

if __name__ == "__main__":
    add_missing_imports()