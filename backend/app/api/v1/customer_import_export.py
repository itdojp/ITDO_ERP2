"""
Customer Import/Export API endpoints for Phase 5 CRM - Data Management.
顧客データインポート/エクスポートAPIエンドポイント（CRM機能Phase 5）
"""

from typing import List, Optional

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Query,
    UploadFile,
    status,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.schemas.customer import CustomerExport, CustomerImport
from app.services.customer_import_export_service import CustomerImportExportService

router = APIRouter()


@router.post("/customers/import/validate")
async def validate_customer_import(
    file: UploadFile = File(..., description="CSV file to validate"),
    mapping: str = Form(..., description="Field mapping configuration as JSON"),
    validation_rules: str = Form("{}", description="Validation rules as JSON"),
    import_mode: str = Form("create", description="Import mode: create/update/upsert"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate customer import data without actually importing."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    try:
        # Read file content
        csv_content = (await file.read()).decode('utf-8')

        # Parse JSON parameters
        import json
        mapping_dict = json.loads(mapping)
        validation_rules_dict = json.loads(validation_rules)

        # Create import configuration
        import_config = CustomerImport(
            file_format="csv",
            mapping=mapping_dict,
            validation_rules=validation_rules_dict,
            import_mode=import_mode
        )

        service = CustomerImportExportService(db)
        validation_result = await service.validate_import_data(
            csv_content=csv_content,
            organization_id=current_user.organization_id,
            import_config=import_config
        )

        return validation_result

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Validation failed: {str(e)}"
        )


@router.post("/customers/import")
async def import_customers(
    file: UploadFile = File(..., description="CSV file to import"),
    mapping: str = Form(..., description="Field mapping configuration as JSON"),
    validation_rules: str = Form("{}", description="Validation rules as JSON"),
    import_mode: str = Form("create", description="Import mode: create/update/upsert"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Import customers from CSV file."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    # Validate file type
    if not file.filename.lower().endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only CSV files are supported"
        )

    try:
        # Read file content
        csv_content = (await file.read()).decode('utf-8')

        # Parse JSON parameters
        import json
        mapping_dict = json.loads(mapping)
        validation_rules_dict = json.loads(validation_rules)

        # Create import configuration
        import_config = CustomerImport(
            file_format="csv",
            mapping=mapping_dict,
            validation_rules=validation_rules_dict,
            import_mode=import_mode
        )

        service = CustomerImportExportService(db)
        import_result = await service.import_customers_from_csv(
            csv_content=csv_content,
            organization_id=current_user.organization_id,
            import_config=import_config,
            created_by=current_user.id
        )

        return import_result

    except json.JSONDecodeError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid JSON in parameters: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.get("/customers/export/csv")
async def export_customers_csv(
    fields: Optional[List[str]] = Query(None, description="Fields to export"),
    customer_type: Optional[str] = Query(None, description="Customer type filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    assigned_to: Optional[int] = Query(None, description="Assigned user filter"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    scale: Optional[str] = Query(None, description="Scale filter"),
    priority: Optional[str] = Query(None, description="Priority filter"),
    city: Optional[str] = Query(None, description="City filter"),
    country: Optional[str] = Query(None, description="Country filter"),
    search_text: Optional[str] = Query(None, description="Text search filter"),
    tags: Optional[str] = Query(None, description="Tags filter"),
    include_contacts: bool = Query(False, description="Include contact information"),
    include_opportunities: bool = Query(False, description="Include opportunities"),
    include_activities: bool = Query(False, description="Include activities"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export customers to CSV format."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    try:
        # Create export configuration
        from app.schemas.customer import CustomerSearch

        filters = CustomerSearch(
            customer_type=customer_type,
            status=status,
            assigned_to=assigned_to,
            industry=industry,
            scale=scale,
            priority=priority,
            city=city,
            country=country,
            search_text=search_text,
            tags=tags
        )

        export_config = CustomerExport(
            format="csv",
            fields=fields or [],
            filters=filters,
            include_contacts=include_contacts,
            include_opportunities=include_opportunities,
            include_activities=include_activities
        )

        service = CustomerImportExportService(db)
        export_result = await service.export_customers_to_csv(
            organization_id=current_user.organization_id,
            export_config=export_config
        )

        if export_result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=export_result["message"]
            )

        # Return CSV as streaming response
        def generate_csv():
            yield export_result["csv_content"]

        return StreamingResponse(
            generate_csv(),
            media_type="text/csv",
            headers={
                "Content-Disposition": (
                    f"attachment; filename={export_result['filename']}"
                )
            }
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export failed: {str(e)}"
        )


@router.get("/customers/export/excel")
async def export_customers_excel(
    fields: Optional[List[str]] = Query(None, description="Fields to export"),
    customer_type: Optional[str] = Query(None, description="Customer type filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    assigned_to: Optional[int] = Query(None, description="Assigned user filter"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    scale: Optional[str] = Query(None, description="Scale filter"),
    priority: Optional[str] = Query(None, description="Priority filter"),
    city: Optional[str] = Query(None, description="City filter"),
    country: Optional[str] = Query(None, description="Country filter"),
    search_text: Optional[str] = Query(None, description="Text search filter"),
    tags: Optional[str] = Query(None, description="Tags filter"),
    include_contacts: bool = Query(False, description="Include contact information"),
    include_opportunities: bool = Query(False, description="Include opportunities"),
    include_activities: bool = Query(False, description="Include activities"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export customers to Excel format."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    try:
        # Create export configuration
        from app.schemas.customer import CustomerSearch

        filters = CustomerSearch(
            customer_type=customer_type,
            status=status,
            assigned_to=assigned_to,
            industry=industry,
            scale=scale,
            priority=priority,
            city=city,
            country=country,
            search_text=search_text,
            tags=tags
        )

        export_config = CustomerExport(
            format="xlsx",
            fields=fields or [],
            filters=filters,
            include_contacts=include_contacts,
            include_opportunities=include_opportunities,
            include_activities=include_activities
        )

        service = CustomerImportExportService(db)
        export_result = await service.export_customers_to_excel(
            organization_id=current_user.organization_id,
            export_config=export_config
        )

        if export_result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=export_result["message"]
            )

        return {
            "status": "success",
            "message": export_result["message"],
            "exported_count": export_result["exported_count"],
            "excel_data": export_result["excel_data"],
            "export_summary": export_result["export_summary"],
            "filename": export_result["filename"]
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Excel export failed: {str(e)}"
        )


@router.get("/customers/import/template")
async def get_import_template(
    format: str = Query("csv", description="Template format: csv/json"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get customer import template with sample data."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    try:
        service = CustomerImportExportService(db)
        template_result = await service.get_import_template(format=format)

        if template_result["status"] != "success":
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=template_result["message"]
            )

        if format.lower() == "csv":
            # Return CSV template as streaming response
            def generate_template():
                yield template_result["template_content"]

            return StreamingResponse(
                generate_template(),
                media_type="text/csv",
                headers={
                    "Content-Disposition": (
                        f"attachment; filename={template_result['filename']}"
                    )
                }
            )
        else:
            # Return JSON template
            return template_result

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Template generation failed: {str(e)}"
        )


@router.get("/customers/import/mapping-guide")
async def get_field_mapping_guide(
    current_user: User = Depends(get_current_user),
):
    """Get field mapping guide for customer import."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    return {
        "mapping_guide": {
            "required_fields": [
                "customer_code",
                "company_name",
                "customer_type"
            ],
            "optional_fields": [
                "name_kana", "short_name", "status", "industry", "scale",
                "email", "phone", "fax", "website", "postal_code",
                "address_line1", "address_line2", "city", "state", "country",
                "annual_revenue", "employee_count", "credit_limit", "payment_terms",
                "priority", "notes", "description", "tags"
            ],
            "field_types": {
                "customer_code": "string",
                "company_name": "string",
                "customer_type": "enum: individual, corporate, government, non_profit",
                "status": "enum: active, inactive, prospect, former",
                "scale": "enum: large, medium, small",
                "priority": "enum: high, normal, low",
                "annual_revenue": "decimal",
                "employee_count": "integer",
                "credit_limit": "decimal"
            },
            "example_mapping": {
                "Company Name": "company_name",
                "Customer Code": "customer_code",
                "Type": "customer_type",
                "Status": "status",
                "Industry": "industry",
                "Email": "email",
                "Phone": "phone"
            }
        },
        "import_modes": {
            "create": "Only create new customers, fail if customer code exists",
            "update": (
                "Only update existing customers, fail if customer code doesn't exist"
            ),
            "upsert": "Create new or update existing customers based on customer code"
        },
        "validation_rules": {
            "required": "Make field required during import",
            "max_length": "Maximum character length for field",
            "format": "Format validation (e.g., email, phone)"
        }
    }


@router.get("/customers/export/summary")
async def get_export_summary(
    customer_type: Optional[str] = Query(None, description="Customer type filter"),
    status: Optional[str] = Query(None, description="Status filter"),
    assigned_to: Optional[int] = Query(None, description="Assigned user filter"),
    industry: Optional[str] = Query(None, description="Industry filter"),
    scale: Optional[str] = Query(None, description="Scale filter"),
    priority: Optional[str] = Query(None, description="Priority filter"),
    city: Optional[str] = Query(None, description="City filter"),
    country: Optional[str] = Query(None, description="Country filter"),
    search_text: Optional[str] = Query(None, description="Text search filter"),
    tags: Optional[str] = Query(None, description="Tags filter"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get summary of customers that would be exported with given filters."""
    if not current_user.organization_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User must belong to an organization"
        )

    try:
        # Create export configuration with minimal fields for counting
        from app.schemas.customer import CustomerSearch

        filters = CustomerSearch(
            customer_type=customer_type,
            status=status,
            assigned_to=assigned_to,
            industry=industry,
            scale=scale,
            priority=priority,
            city=city,
            country=country,
            search_text=search_text,
            tags=tags
        )

        export_config = CustomerExport(
            format="csv",
            fields=["customer_code"],  # Minimal field for counting
            filters=filters,
            include_contacts=False,
            include_opportunities=False,
            include_activities=False
        )

        service = CustomerImportExportService(db)
        export_result = await service.export_customers_to_csv(
            organization_id=current_user.organization_id,
            export_config=export_config
        )

        return {
            "estimated_export_count": export_result.get("exported_count", 0),
            "applied_filters": {
                "customer_type": customer_type,
                "status": status,
                "assigned_to": assigned_to,
                "industry": industry,
                "scale": scale,
                "priority": priority,
                "city": city,
                "country": country,
                "search_text": search_text,
                "tags": tags
            }
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Export summary failed: {str(e)}"
        )
