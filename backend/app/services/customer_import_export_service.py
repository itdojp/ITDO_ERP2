"""
Customer Import/Export Service for Phase 5 CRM - Data Management.
顧客データインポート/エクスポートサービス（CRM機能Phase 5）
"""

import csv
import io
import json
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.customer import Customer
from app.schemas.customer import (
    CustomerExport,
    CustomerImport,
    CustomerResponse,
)


class CustomerImportExportService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def import_customers_from_csv(
        self,
        csv_content: str,
        organization_id: int,
        import_config: CustomerImport,
        created_by: int,
    ) -> Dict:
        """Import customers from CSV data."""
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            csv_data = list(csv_reader)

            if not csv_data:
                return {
                    "status": "error",
                    "message": "No data found in CSV file",
                    "imported_count": 0,
                    "error_count": 0,
                    "errors": [],
                }

            # Validate mapping configuration
            validation_result = self._validate_import_mapping(
                csv_data[0].keys(), import_config.mapping
            )
            if not validation_result["valid"]:
                return {
                    "status": "error",
                    "message": "Invalid field mapping",
                    "errors": validation_result["errors"],
                    "imported_count": 0,
                    "error_count": len(csv_data),
                }

            # Process each row
            imported_customers = []
            import_errors = []

            for row_index, row_data in enumerate(csv_data):
                try:
                    # Transform row data according to mapping
                    customer_data = self._transform_row_data(
                        row_data, import_config.mapping
                    )

                    # Validate customer data
                    validation_errors = await self._validate_customer_data(
                        customer_data, organization_id, import_config.validation_rules
                    )

                    if validation_errors:
                        import_errors.append({
                            "row": row_index + 2,  # +2 for header and 0-based index
                            "errors": validation_errors,
                            "data": row_data,
                        })
                        continue

                    # Create or update customer based on import mode
                    if import_config.import_mode == "create":
                        customer = await self._create_customer(
                            customer_data, organization_id, created_by
                        )
                    elif import_config.import_mode == "update":
                        customer = await self._update_customer(
                            customer_data, organization_id
                        )
                    elif import_config.import_mode == "upsert":
                        customer = await self._upsert_customer(
                            customer_data, organization_id, created_by
                        )
                    else:
                        raise ValueError(f"Invalid import mode: {import_config.import_mode}")

                    if customer:
                        imported_customers.append(customer)

                except Exception as e:
                    import_errors.append({
                        "row": row_index + 2,
                        "errors": [str(e)],
                        "data": row_data,
                    })

            # Commit changes
            await self.db.commit()

            return {
                "status": "success" if not import_errors else "partial_success",
                "message": f"Import completed. {len(imported_customers)} customers imported, {len(import_errors)} errors.",
                "imported_count": len(imported_customers),
                "error_count": len(import_errors),
                "imported_customers": [
                    CustomerResponse.model_validate(customer)
                    for customer in imported_customers
                ],
                "errors": import_errors,
                "import_summary": {
                    "total_rows": len(csv_data),
                    "successful_imports": len(imported_customers),
                    "failed_imports": len(import_errors),
                    "import_mode": import_config.import_mode,
                },
            }

        except Exception as e:
            await self.db.rollback()
            return {
                "status": "error",
                "message": f"Import failed: {str(e)}",
                "imported_count": 0,
                "error_count": 0,
                "errors": [{"general_error": str(e)}],
            }

    async def export_customers_to_csv(
        self,
        organization_id: int,
        export_config: CustomerExport,
    ) -> Dict:
        """Export customers to CSV format."""
        try:
            # Build query based on filters
            customers_query = (
                select(Customer)
                .where(
                    and_(
                        Customer.organization_id == organization_id,
                        Customer.deleted_at.is_(None),
                    )
                )
                .options(
                    selectinload(Customer.contacts),
                    selectinload(Customer.opportunities),
                    selectinload(Customer.assigned_user),
                )
            )

            # Apply filters if provided
            if export_config.filters:
                customers_query = self._apply_export_filters(
                    customers_query, export_config.filters
                )

            customers_result = await self.db.execute(customers_query)
            customers = customers_result.scalars().all()

            if not customers:
                return {
                    "status": "error",
                    "message": "No customers found for export",
                    "exported_count": 0,
                }

            # Determine fields to export
            export_fields = export_config.fields or self._get_default_export_fields()

            # Generate CSV content
            csv_content = self._generate_csv_content(
                customers, export_fields, export_config
            )

            return {
                "status": "success",
                "message": f"Export completed. {len(customers)} customers exported.",
                "exported_count": len(customers),
                "csv_content": csv_content,
                "export_summary": {
                    "total_customers": len(customers),
                    "fields_exported": len(export_fields),
                    "include_contacts": export_config.include_contacts,
                    "include_opportunities": export_config.include_opportunities,
                    "include_activities": export_config.include_activities,
                },
                "filename": f"customers_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Export failed: {str(e)}",
                "exported_count": 0,
            }

    async def export_customers_to_excel(
        self,
        organization_id: int,
        export_config: CustomerExport,
    ) -> Dict:
        """Export customers to Excel format."""
        try:
            # Get customers data similar to CSV export
            customers_query = (
                select(Customer)
                .where(
                    and_(
                        Customer.organization_id == organization_id,
                        Customer.deleted_at.is_(None),
                    )
                )
                .options(
                    selectinload(Customer.contacts),
                    selectinload(Customer.opportunities),
                    selectinload(Customer.assigned_user),
                )
            )

            if export_config.filters:
                customers_query = self._apply_export_filters(
                    customers_query, export_config.filters
                )

            customers_result = await self.db.execute(customers_query)
            customers = customers_result.scalars().all()

            if not customers:
                return {
                    "status": "error",
                    "message": "No customers found for export",
                    "exported_count": 0,
                }

            export_fields = export_config.fields or self._get_default_export_fields()

            # Generate Excel data structure
            excel_data = self._generate_excel_data(
                customers, export_fields, export_config
            )

            return {
                "status": "success",
                "message": f"Excel export completed. {len(customers)} customers exported.",
                "exported_count": len(customers),
                "excel_data": excel_data,
                "export_summary": {
                    "total_customers": len(customers),
                    "fields_exported": len(export_fields),
                    "sheets_created": len(excel_data),
                },
                "filename": f"customers_export_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx",
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Excel export failed: {str(e)}",
                "exported_count": 0,
            }

    async def validate_import_data(
        self,
        csv_content: str,
        organization_id: int,
        import_config: CustomerImport,
    ) -> Dict:
        """Validate import data without actually importing."""
        try:
            # Parse CSV content
            csv_reader = csv.DictReader(io.StringIO(csv_content))
            csv_data = list(csv_reader)

            if not csv_data:
                return {
                    "status": "error",
                    "message": "No data found in CSV file",
                    "valid_rows": 0,
                    "invalid_rows": 0,
                    "validation_errors": [],
                }

            # Validate mapping
            validation_result = self._validate_import_mapping(
                csv_data[0].keys(), import_config.mapping
            )
            if not validation_result["valid"]:
                return {
                    "status": "error",
                    "message": "Invalid field mapping",
                    "mapping_errors": validation_result["errors"],
                    "valid_rows": 0,
                    "invalid_rows": len(csv_data),
                }

            # Validate each row
            validation_errors = []
            valid_count = 0

            for row_index, row_data in enumerate(csv_data):
                try:
                    customer_data = self._transform_row_data(
                        row_data, import_config.mapping
                    )

                    row_errors = await self._validate_customer_data(
                        customer_data, organization_id, import_config.validation_rules
                    )

                    if row_errors:
                        validation_errors.append({
                            "row": row_index + 2,
                            "errors": row_errors,
                            "data": row_data,
                        })
                    else:
                        valid_count += 1

                except Exception as e:
                    validation_errors.append({
                        "row": row_index + 2,
                        "errors": [str(e)],
                        "data": row_data,
                    })

            return {
                "status": "success",
                "message": f"Validation completed. {valid_count} valid rows, {len(validation_errors)} invalid rows.",
                "valid_rows": valid_count,
                "invalid_rows": len(validation_errors),
                "total_rows": len(csv_data),
                "validation_errors": validation_errors,
                "validation_summary": {
                    "mapping_valid": True,
                    "data_quality_score": (valid_count / len(csv_data) * 100) if csv_data else 0,
                    "recommended_action": (
                        "proceed_with_import" if len(validation_errors) == 0
                        else "review_errors" if len(validation_errors) < len(csv_data) * 0.1
                        else "fix_data_issues"
                    ),
                },
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Validation failed: {str(e)}",
                "valid_rows": 0,
                "invalid_rows": 0,
                "validation_errors": [{"general_error": str(e)}],
            }

    async def get_import_template(self, format: str = "csv") -> Dict:
        """Generate import template with sample data."""
        template_fields = {
            "customer_code": "CUST001",
            "company_name": "Sample Company Ltd.",
            "name_kana": "サンプルカイシャ",
            "short_name": "Sample Co.",
            "customer_type": "corporate",
            "status": "prospect",
            "industry": "Technology",
            "scale": "medium",
            "email": "contact@sample.com",
            "phone": "03-1234-5678",
            "fax": "03-1234-5679",
            "website": "https://www.sample.com",
            "postal_code": "100-0001",
            "address_line1": "1-1-1 Chiyoda",
            "address_line2": "Sample Building 5F",
            "city": "Tokyo",
            "state": "Tokyo",
            "country": "Japan",
            "annual_revenue": "100000000",
            "employee_count": "100",
            "credit_limit": "5000000",
            "payment_terms": "Net 30",
            "priority": "normal",
            "notes": "Sample customer for import template",
            "description": "Sample company description",
            "tags": "sample,template,test",
        }

        if format.lower() == "csv":
            # Generate CSV template
            csv_output = io.StringIO()
            writer = csv.DictWriter(csv_output, fieldnames=template_fields.keys())
            writer.writeheader()
            writer.writerow(template_fields)

            return {
                "status": "success",
                "format": "csv",
                "template_content": csv_output.getvalue(),
                "filename": "customer_import_template.csv",
                "field_descriptions": self._get_field_descriptions(),
            }

        elif format.lower() == "json":
            return {
                "status": "success",
                "format": "json",
                "template_content": json.dumps([template_fields], indent=2),
                "filename": "customer_import_template.json",
                "field_descriptions": self._get_field_descriptions(),
            }

        else:
            return {
                "status": "error",
                "message": f"Unsupported template format: {format}",
            }

    def _validate_import_mapping(
        self, csv_headers: List[str], mapping: Dict
    ) -> Dict:
        """Validate field mapping configuration."""
        errors = []
        required_fields = ["customer_code", "company_name", "customer_type"]

        # Check if required fields are mapped
        for field in required_fields:
            if field not in mapping.values():
                errors.append(f"Required field '{field}' is not mapped")

        # Check if mapped CSV headers exist
        for csv_header, db_field in mapping.items():
            if csv_header not in csv_headers:
                errors.append(f"CSV header '{csv_header}' not found in file")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
        }

    def _transform_row_data(self, row_data: Dict, mapping: Dict) -> Dict:
        """Transform CSV row data to customer data structure."""
        customer_data = {}

        for csv_field, db_field in mapping.items():
            value = row_data.get(csv_field, "").strip()
            if value:
                # Type conversion based on field
                if db_field in ["annual_revenue", "credit_limit"]:
                    try:
                        customer_data[db_field] = Decimal(value)
                    except:
                        customer_data[db_field] = None
                elif db_field == "employee_count":
                    try:
                        customer_data[db_field] = int(value)
                    except:
                        customer_data[db_field] = None
                else:
                    customer_data[db_field] = value

        return customer_data

    async def _validate_customer_data(
        self, customer_data: Dict, organization_id: int, validation_rules: Dict
    ) -> List[str]:
        """Validate customer data against business rules."""
        errors = []

        # Required field validation
        required_fields = ["customer_code", "company_name", "customer_type"]
        for field in required_fields:
            if not customer_data.get(field):
                errors.append(f"Required field '{field}' is missing or empty")

        # Customer code uniqueness check
        if customer_data.get("customer_code"):
            existing_query = select(Customer).where(
                and_(
                    Customer.customer_code == customer_data["customer_code"],
                    Customer.organization_id == organization_id,
                    Customer.deleted_at.is_(None),
                )
            )
            existing_result = await self.db.execute(existing_query)
            existing_customer = existing_result.scalar_one_or_none()

            if existing_customer:
                errors.append(f"Customer code '{customer_data['customer_code']}' already exists")

        # Enum validation
        valid_customer_types = ["individual", "corporate", "government", "non_profit"]
        if customer_data.get("customer_type") and customer_data["customer_type"] not in valid_customer_types:
            errors.append(f"Invalid customer_type. Must be one of: {', '.join(valid_customer_types)}")

        valid_statuses = ["active", "inactive", "prospect", "former"]
        if customer_data.get("status") and customer_data["status"] not in valid_statuses:
            errors.append(f"Invalid status. Must be one of: {', '.join(valid_statuses)}")

        valid_scales = ["large", "medium", "small"]
        if customer_data.get("scale") and customer_data["scale"] not in valid_scales:
            errors.append(f"Invalid scale. Must be one of: {', '.join(valid_scales)}")

        valid_priorities = ["high", "normal", "low"]
        if customer_data.get("priority") and customer_data["priority"] not in valid_priorities:
            errors.append(f"Invalid priority. Must be one of: {', '.join(valid_priorities)}")

        # Custom validation rules
        for field, rule in validation_rules.items():
            if field in customer_data:
                value = customer_data[field]
                if rule.get("required") and not value:
                    errors.append(f"Field '{field}' is required by validation rules")

                if rule.get("max_length") and isinstance(value, str) and len(value) > rule["max_length"]:
                    errors.append(f"Field '{field}' exceeds maximum length of {rule['max_length']}")

        return errors

    async def _create_customer(
        self, customer_data: Dict, organization_id: int, created_by: int
    ) -> Customer:
        """Create new customer from imported data."""
        customer = Customer(
            organization_id=organization_id,
            created_by=created_by,
            **customer_data
        )

        self.db.add(customer)
        await self.db.flush()
        await self.db.refresh(customer)

        return customer

    async def _update_customer(
        self, customer_data: Dict, organization_id: int
    ) -> Optional[Customer]:
        """Update existing customer from imported data."""
        if not customer_data.get("customer_code"):
            raise ValueError("Customer code required for update mode")

        query = select(Customer).where(
            and_(
                Customer.customer_code == customer_data["customer_code"],
                Customer.organization_id == organization_id,
                Customer.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        customer = result.scalar_one_or_none()

        if not customer:
            raise ValueError(f"Customer with code '{customer_data['customer_code']}' not found")

        # Update fields
        for field, value in customer_data.items():
            if field != "customer_code" and hasattr(customer, field):
                setattr(customer, field, value)

        customer.updated_at = datetime.utcnow()
        await self.db.flush()
        await self.db.refresh(customer)

        return customer

    async def _upsert_customer(
        self, customer_data: Dict, organization_id: int, created_by: int
    ) -> Customer:
        """Create or update customer (upsert mode)."""
        try:
            # Try to update first
            return await self._update_customer(customer_data, organization_id)
        except ValueError:
            # If not found, create new
            return await self._create_customer(customer_data, organization_id, created_by)

    def _apply_export_filters(self, query, filters):
        """Apply export filters to customer query."""
        if filters.customer_type:
            query = query.where(Customer.customer_type == filters.customer_type)

        if filters.status:
            query = query.where(Customer.status == filters.status)

        if filters.assigned_to:
            query = query.where(Customer.assigned_to == filters.assigned_to)

        if filters.industry:
            query = query.where(Customer.industry == filters.industry)

        if filters.scale:
            query = query.where(Customer.scale == filters.scale)

        if filters.priority:
            query = query.where(Customer.priority == filters.priority)

        if filters.city:
            query = query.where(Customer.city == filters.city)

        if filters.country:
            query = query.where(Customer.country == filters.country)

        if filters.search_text:
            search_pattern = f"%{filters.search_text}%"
            query = query.where(
                Customer.company_name.ilike(search_pattern)
                | Customer.notes.ilike(search_pattern)
                | Customer.description.ilike(search_pattern)
            )

        if filters.tags:
            query = query.where(Customer.tags.ilike(f"%{filters.tags}%"))

        return query

    def _get_default_export_fields(self) -> List[str]:
        """Get default fields for export."""
        return [
            "customer_code",
            "company_name",
            "name_kana",
            "short_name",
            "customer_type",
            "status",
            "industry",
            "scale",
            "email",
            "phone",
            "fax",
            "website",
            "postal_code",
            "address_line1",
            "address_line2",
            "city",
            "state",
            "country",
            "annual_revenue",
            "employee_count",
            "credit_limit",
            "payment_terms",
            "priority",
            "notes",
            "description",
            "tags",
            "first_contact_date",
            "last_contact_date",
            "total_sales",
            "total_transactions",
            "created_at",
            "updated_at",
        ]

    def _generate_csv_content(
        self, customers: List[Customer], export_fields: List[str], export_config: CustomerExport
    ) -> str:
        """Generate CSV content from customer data."""
        output = io.StringIO()

        # Prepare headers
        headers = export_fields.copy()
        if export_config.include_contacts:
            headers.extend(["primary_contact_name", "primary_contact_email", "primary_contact_phone"])
        if export_config.include_opportunities:
            headers.extend(["open_opportunities_count", "total_opportunity_value"])

        writer = csv.DictWriter(output, fieldnames=headers)
        writer.writeheader()

        # Write customer data
        for customer in customers:
            row_data = {}

            # Basic customer fields
            for field in export_fields:
                value = getattr(customer, field, None)
                if isinstance(value, Decimal):
                    row_data[field] = str(value)
                elif isinstance(value, datetime):
                    row_data[field] = value.isoformat() if value else ""
                else:
                    row_data[field] = str(value) if value is not None else ""

            # Additional data based on configuration
            if export_config.include_contacts and customer.contacts:
                primary_contact = next(
                    (contact for contact in customer.contacts if contact.is_primary),
                    customer.contacts[0] if customer.contacts else None
                )
                if primary_contact:
                    row_data["primary_contact_name"] = primary_contact.name
                    row_data["primary_contact_email"] = primary_contact.email or ""
                    row_data["primary_contact_phone"] = primary_contact.phone or ""

            if export_config.include_opportunities and customer.opportunities:
                open_opps = [opp for opp in customer.opportunities if opp.is_open]
                row_data["open_opportunities_count"] = len(open_opps)
                row_data["total_opportunity_value"] = str(
                    sum(float(opp.value or 0) for opp in open_opps)
                )

            writer.writerow(row_data)

        return output.getvalue()

    def _generate_excel_data(
        self, customers: List[Customer], export_fields: List[str], export_config: CustomerExport
    ) -> Dict:
        """Generate Excel data structure from customer data."""
        excel_data = {}

        # Main customers sheet
        customers_data = []
        for customer in customers:
            row_data = {}
            for field in export_fields:
                value = getattr(customer, field, None)
                if isinstance(value, Decimal):
                    row_data[field] = float(value)
                elif isinstance(value, datetime):
                    row_data[field] = value.isoformat() if value else ""
                else:
                    row_data[field] = str(value) if value is not None else ""
            customers_data.append(row_data)

        excel_data["customers"] = {
            "headers": export_fields,
            "data": customers_data,
        }

        # Additional sheets based on configuration
        if export_config.include_contacts:
            contacts_data = []
            for customer in customers:
                for contact in customer.contacts:
                    contacts_data.append({
                        "customer_code": customer.customer_code,
                        "customer_name": customer.company_name,
                        "contact_name": contact.name,
                        "contact_email": contact.email or "",
                        "contact_phone": contact.phone or "",
                        "contact_title": contact.title or "",
                        "contact_department": contact.department or "",
                        "is_primary": contact.is_primary,
                        "is_decision_maker": contact.is_decision_maker,
                    })

            excel_data["contacts"] = {
                "headers": [
                    "customer_code", "customer_name", "contact_name", "contact_email",
                    "contact_phone", "contact_title", "contact_department",
                    "is_primary", "is_decision_maker"
                ],
                "data": contacts_data,
            }

        if export_config.include_opportunities:
            opportunities_data = []
            for customer in customers:
                for opportunity in customer.opportunities:
                    opportunities_data.append({
                        "customer_code": customer.customer_code,
                        "customer_name": customer.company_name,
                        "opportunity_name": opportunity.name,
                        "opportunity_stage": opportunity.stage.value,
                        "opportunity_value": float(opportunity.value or 0),
                        "probability": opportunity.probability,
                        "expected_close_date": (
                            opportunity.expected_close_date.isoformat()
                            if opportunity.expected_close_date else ""
                        ),
                        "status": opportunity.status,
                    })

            excel_data["opportunities"] = {
                "headers": [
                    "customer_code", "customer_name", "opportunity_name",
                    "opportunity_stage", "opportunity_value", "probability",
                    "expected_close_date", "status"
                ],
                "data": opportunities_data,
            }

        return excel_data

    def _get_field_descriptions(self) -> Dict:
        """Get field descriptions for import template."""
        return {
            "customer_code": "Unique customer identifier (required)",
            "company_name": "Company/organization name (required)",
            "name_kana": "Company name in katakana (Japanese)",
            "short_name": "Abbreviated company name",
            "customer_type": "Type: individual, corporate, government, non_profit (required)",
            "status": "Status: active, inactive, prospect, former",
            "industry": "Industry sector",
            "scale": "Company size: large, medium, small",
            "email": "Primary email address",
            "phone": "Primary phone number",
            "fax": "FAX number",
            "website": "Company website URL",
            "postal_code": "Postal/ZIP code",
            "address_line1": "Primary address line",
            "address_line2": "Secondary address line",
            "city": "City",
            "state": "State/Prefecture",
            "country": "Country",
            "annual_revenue": "Annual revenue in numbers",
            "employee_count": "Number of employees",
            "credit_limit": "Credit limit amount",
            "payment_terms": "Payment terms description",
            "priority": "Priority level: high, normal, low",
            "notes": "Customer notes",
            "description": "General description",
            "tags": "Comma-separated tags",
        }
