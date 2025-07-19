"""Data export/import service for CSV, Excel, and PDF generation."""

import csv
import io
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import pandas as pd
from fastapi import BackgroundTasks, HTTPException
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Table, TableStyle
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.export_job import ExportJob, ExportStatus
from app.schemas.data_export import (
    ExportJobCreate,
    ExportJobResponse,
    ExportProgressResponse,
    ImportJobCreate,
    ImportJobResponse,
    ImportValidationResponse,
)


class DataExportService:
    """Service for data export and import operations."""

    SUPPORTED_FORMATS = ["csv", "excel", "pdf", "json"]
    MAX_ROWS_SYNC = 1000  # Maximum rows for synchronous export

    def __init__(self, db: Session):
        """Initialize export service."""
        self.db = db

    async def create_export_job(
        self,
        export_data: ExportJobCreate,
        created_by: int,
        background_tasks: Optional[BackgroundTasks] = None,
    ) -> ExportJobResponse:
        """Create a new export job."""
        # Validate export format
        if export_data.format not in self.SUPPORTED_FORMATS:
            raise HTTPException(
                status_code=400,
                detail=(
                    "Unsupported format. Supported: "
                    f"{', '.join(self.SUPPORTED_FORMATS)}"
                ),
            )

        # Create export job record
        job = ExportJob(
            entity_type=export_data.entity_type,
            format=export_data.format,
            filters=export_data.filters or {},
            columns=export_data.columns or [],
            status=ExportStatus.PENDING,
            created_by=created_by,
            organization_id=export_data.organization_id,
            configuration=export_data.configuration or {},
        )

        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)

        # Determine if export should be synchronous or background
        estimated_rows = await self._estimate_export_size(export_data)

        if estimated_rows <= self.MAX_ROWS_SYNC and not background_tasks:
            # Execute synchronously for small exports
            await self._execute_export_sync(job.id)
        elif background_tasks:
            # Execute in background
            background_tasks.add_task(self._execute_export_background, job.id)
        else:
            # Mark as queued for manual processing
            job.status = ExportStatus.QUEUED
            self.db.commit()

        return self._job_to_response(job)

    async def get_export_job(self, job_id: int) -> Optional[ExportJobResponse]:
        """Get export job by ID."""
        job = self.db.query(ExportJob).filter(ExportJob.id == job_id).first()
        if not job:
            return None

        return self._job_to_response(job)

    async def get_export_progress(
        self, job_id: int
    ) -> Optional[ExportProgressResponse]:
        """Get export job progress."""
        job = self.db.query(ExportJob).filter(ExportJob.id == job_id).first()
        if not job:
            return None

        return ExportProgressResponse(
            job_id=job.id,
            status=job.status,
            progress_percentage=job.progress_percentage or 0,
            rows_processed=job.rows_processed or 0,
            total_rows=job.total_rows or 0,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    async def download_export(self, job_id: int) -> Optional[tuple[bytes, str, str]]:
        """Download completed export file."""
        job = self.db.query(ExportJob).filter(ExportJob.id == job_id).first()
        if not job or job.status != ExportStatus.COMPLETED:
            return None

        if not job.file_path or not Path(job.file_path).exists():
            return None

        try:
            with open(job.file_path, "rb") as f:
                content = f.read()

            filename = f"{job.entity_type}_export_{job.id}.{job.format}"
            mime_type = self._get_mime_type(job.format)

            return content, filename, mime_type
        except Exception:
            return None

    async def export_to_csv(
        self,
        entity_type: str,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
    ) -> str:
        """Export data to CSV format."""
        if not data:
            return ""

        # Use specified columns or all available keys
        if columns:
            fieldnames = columns
        else:
            fieldnames = list(data[0].keys()) if data else []

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()

        for row in data:
            # Filter row to only include specified columns
            filtered_row = {k: v for k, v in row.items() if k in fieldnames}
            writer.writerow(filtered_row)

        return output.getvalue()

    async def export_to_excel(
        self,
        entity_type: str,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
    ) -> bytes:
        """Export data to Excel format."""
        if not data:
            # Create empty DataFrame
            df = pd.DataFrame()
        else:
            df = pd.DataFrame(data)

            # Filter columns if specified
            if columns:
                available_columns = [col for col in columns if col in df.columns]
                df = df[available_columns]

        # Create Excel file in memory
        output = io.BytesIO()

        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name=entity_type.capitalize(), index=False)

            # Add metadata sheet
            metadata_df = pd.DataFrame(
                {
                    "Property": ["Export Date", "Entity Type", "Total Records"],
                    "Value": [datetime.utcnow().isoformat(), entity_type, len(data)],
                }
            )
            metadata_df.to_excel(writer, sheet_name="Metadata", index=False)

        output.seek(0)
        return output.getvalue()

    async def export_to_pdf(
        self,
        entity_type: str,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
    ) -> bytes:
        """Export data to PDF format."""
        output = io.BytesIO()
        doc = SimpleDocTemplate(output, pagesize=letter)

        # Get styles
        styles = getSampleStyleSheet()

        # Create story (content)
        story: list[Flowable] = []

        # Add title
        title = Paragraph(f"{entity_type.title()} Export Report", styles["Title"])
        story.append(title)

        # Add metadata
        metadata_text = (
            f"Generated on: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')}"
            f"<br/>Total Records: {len(data)}"
        )
        metadata = Paragraph(metadata_text, styles["Normal"])
        story.append(metadata)
        story.append(Paragraph("<br/>", styles["Normal"]))  # Spacing

        if not data:
            no_data = Paragraph("No data available for export.", styles["Normal"])
            story.append(no_data)
        else:
            # Prepare table data
            if columns:
                headers = columns
                available_columns = [col for col in columns if col in data[0].keys()]
            else:
                available_columns = list(data[0].keys())
                headers = available_columns

            # Limit columns for PDF readability
            if len(headers) > 6:
                headers = headers[:6]
                available_columns = available_columns[:6]

            table_data = [headers]  # Header row

            # Add data rows (limit for PDF)
            max_rows = min(len(data), 50)  # Limit to 50 rows for PDF
            for i in range(max_rows):
                row = data[i]
                table_row = [str(row.get(col, "")) for col in available_columns]
                table_data.append(table_row)

            # Create table
            table = Table(table_data)
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
                        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
                        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                        ("FONTSIZE", (0, 0), (-1, 0), 10),
                        ("BOTTOMPADDING", (0, 0), (-1, 0), 12),
                        ("BACKGROUND", (0, 1), (-1, -1), colors.beige),
                        ("FONTSIZE", (0, 1), (-1, -1), 8),
                        ("GRID", (0, 0), (-1, -1), 1, colors.black),
                    ]
                )
            )

            story.append(table)

            # Add note if data was truncated
            if len(data) > max_rows:
                note = Paragraph(
                    (
                        f"<br/>Note: Only first {max_rows} records shown. "
                        f"Total records: {len(data)}"
                    ),
                    styles["Italic"],
                )
                story.append(note)

        # Build PDF
        doc.build(story)
        output.seek(0)
        return output.getvalue()

    async def export_to_json(
        self,
        entity_type: str,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
    ) -> str:
        """Export data to JSON format."""
        if not data:
            export_data = []
        else:
            if columns:
                # Filter data to only include specified columns
                export_data = [
                    {k: v for k, v in row.items() if k in columns} for row in data
                ]
            else:
                export_data = data

        # Create structured JSON with metadata
        result = {
            "metadata": {
                "entity_type": entity_type,
                "export_date": datetime.utcnow().isoformat(),
                "total_records": len(export_data),
                "columns": columns or (list(data[0].keys()) if data else []),
            },
            "data": export_data,
        }

        return json.dumps(result, indent=2, default=str)

    async def validate_import_data(
        self,
        entity_type: str,
        file_content: bytes,
        file_format: str,
    ) -> ImportValidationResponse:
        """Validate import data before processing."""
        try:
            # Parse data based on format
            if file_format == "csv":
                data = self._parse_csv_data(file_content)
            elif file_format == "excel":
                data = self._parse_excel_data(file_content)
            elif file_format == "json":
                data = self._parse_json_data(file_content)
            else:
                return ImportValidationResponse(
                    valid=False,
                    error="Unsupported file format",
                    total_rows=0,
                    valid_rows=0,
                    errors=[],
                )

            # Validate data structure
            validation_errors = []
            valid_rows = 0

            for i, row in enumerate(data):
                row_errors = self._validate_row(entity_type, row, i + 1)
                if row_errors:
                    validation_errors.extend(row_errors)
                else:
                    valid_rows += 1

            return ImportValidationResponse(
                valid=len(validation_errors) == 0,
                total_rows=len(data),
                valid_rows=valid_rows,
                errors=validation_errors,
                sample_data=data[:5],  # First 5 rows as sample
            )

        except Exception as e:
            return ImportValidationResponse(
                valid=False,
                error=f"Failed to parse file: {str(e)}",
                total_rows=0,
                valid_rows=0,
                errors=[],
            )

    async def import_data(
        self,
        import_data: ImportJobCreate,
        created_by: int,
    ) -> ImportJobResponse:
        """Import data from file."""
        # This is a placeholder implementation
        # In a full implementation, this would:
        # 1. Create an import job record
        # 2. Validate the data
        # 3. Process the import (possibly in background)
        # 4. Return job status

        return ImportJobResponse(
            id=1,  # Placeholder
            entity_type=import_data.entity_type,
            status="pending",
            total_rows=0,
            processed_rows=0,
            error_rows=0,
            created_at=datetime.utcnow(),
        )

    # Private methods

    async def _execute_export_sync(self, job_id: int) -> None:
        """Execute export job synchronously."""
        job = self.db.query(ExportJob).filter(ExportJob.id == job_id).first()
        if not job:
            return

        try:
            job.status = ExportStatus.RUNNING
            job.started_at = datetime.utcnow()
            self.db.commit()

            # Get data to export
            data = await self._fetch_export_data(job)

            # Generate export file
            file_path = await self._generate_export_file(job, data)

            # Update job with results
            job.status = ExportStatus.COMPLETED
            job.completed_at = datetime.utcnow()
            job.file_path = file_path
            job.rows_processed = len(data)
            job.total_rows = len(data)
            job.progress_percentage = 100

        except Exception as e:
            job.status = ExportStatus.FAILED
            job.error_message = str(e)
            job.completed_at = datetime.utcnow()

        self.db.commit()

    async def _execute_export_background(self, job_id: int) -> None:
        """Execute export job in background."""
        await self._execute_export_sync(job_id)

    async def _fetch_export_data(self, job: ExportJob) -> List[Dict[str, Any]]:
        """Fetch data for export based on job configuration."""
        # This is a simplified implementation
        # In practice, this would query the appropriate tables/models

        base_query = f"SELECT * FROM {job.entity_type}"
        where_conditions = []

        # Apply filters
        for key, value in job.filters.items():
            if isinstance(value, str):
                where_conditions.append(f"{key} = '{value}'")
            else:
                where_conditions.append(f"{key} = {value}")

        if where_conditions:
            base_query += " WHERE " + " AND ".join(where_conditions)

        # Add organization filter if specified
        if job.organization_id:
            if where_conditions:
                base_query += f" AND organization_id = {job.organization_id}"
            else:
                base_query += f" WHERE organization_id = {job.organization_id}"

        try:
            result = self.db.execute(text(base_query))
            columns = result.keys()
            rows = result.fetchall()

            return [dict(zip(columns, row)) for row in rows]
        except Exception:
            # Fallback to empty data if query fails
            return []

    async def _generate_export_file(
        self, job: ExportJob, data: List[Dict[str, Any]]
    ) -> str:
        """Generate export file and return file path."""
        # Create exports directory
        export_dir = Path("exports")
        export_dir.mkdir(exist_ok=True)

        filename = f"{job.entity_type}_export_{job.id}.{job.format}"
        file_path = export_dir / filename

        if job.format == "csv":
            csv_content = await self.export_to_csv(job.entity_type, data, job.columns)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(csv_content)

        elif job.format == "excel":
            excel_content = await self.export_to_excel(
                job.entity_type, data, job.columns
            )
            with open(file_path, "wb") as f:
                f.write(excel_content)

        elif job.format == "pdf":
            pdf_content = await self.export_to_pdf(job.entity_type, data, job.columns)
            with open(file_path, "wb") as f:
                f.write(pdf_content)

        elif job.format == "json":
            content = await self.export_to_json(job.entity_type, data, job.columns)
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

        return str(file_path)

    async def _estimate_export_size(self, export_data: ExportJobCreate) -> int:
        """Estimate the number of rows for export."""
        # Simplified estimation - in practice, this would run a COUNT query
        return 100  # Placeholder

    def _get_mime_type(self, format: str) -> str:
        """Get MIME type for export format."""
        mime_types = {
            "csv": "text/csv",
            "excel": (
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            ),
            "pdf": "application/pdf",
            "json": "application/json",
        }
        return mime_types.get(format, "application/octet-stream")

    def _job_to_response(self, job: ExportJob) -> ExportJobResponse:
        """Convert export job to response schema."""
        return ExportJobResponse(
            id=job.id,
            entity_type=job.entity_type,
            format=job.format,
            status=job.status,
            progress_percentage=job.progress_percentage or 0,
            rows_processed=job.rows_processed or 0,
            total_rows=job.total_rows or 0,
            file_path=job.file_path,
            error_message=job.error_message,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
        )

    def _parse_csv_data(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse CSV data from bytes."""
        csv_text = content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(csv_text))
        return list(reader)

    def _parse_excel_data(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse Excel data from bytes."""
        df = pd.read_excel(io.BytesIO(content))
        return cast("List[Dict[str, Any]]", df.to_dict("records"))

    def _parse_json_data(self, content: bytes) -> List[Dict[str, Any]]:
        """Parse JSON data from bytes."""
        json_text = content.decode("utf-8")
        data = json.loads(json_text)

        # Handle different JSON structures
        if isinstance(data, list):
            return data
        elif isinstance(data, dict) and "data" in data:
            return cast("list[dict[str, Any]]", data["data"])
        else:
            return [data]

    def _validate_row(
        self, entity_type: str, row: Dict[str, Any], row_number: int
    ) -> List[str]:
        """Validate a single row of import data."""
        errors = []

        # Basic validation - in practice, this would be entity-specific
        if not row:
            errors.append(f"Row {row_number}: Empty row")

        # Add more validation rules based on entity_type

        return errors
