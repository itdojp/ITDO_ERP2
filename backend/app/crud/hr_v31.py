"""
HR CRUD Operations - CC02 v31.0 Phase 2

Comprehensive CRUD operations for human resources management including:
- Employee Management
- Position/Job Management
- Payroll Processing
- Performance Management
- Leave Management
- Training & Development
- Benefits Administration
- Recruitment Management
- Employee Onboarding
- HR Analytics
"""

from datetime import datetime, date, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional

from sqlalchemy import and_, desc, func, or_
from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.hr_extended import (
    Employee,
    EmployeeStatus,
    EmploymentType,
    HRAnalytics,
    JobPosting,
    LeaveRequest,
    LeaveStatus,
    LeaveType,
    OnboardingRecord,
    PayFrequency,
    PayrollRecord,
    PerformanceReview,
    PerformanceRating,
    Position,
    RecruitmentStatus,
    TrainingRecord,
    TrainingStatus,
    EmployeeBenefit,
)
from app.schemas.hr_v31 import (
    EmployeeCreate,
    EmployeeUpdate,
    JobPostingCreate,
    JobPostingUpdate,
    LeaveRequestCreate,
    LeaveRequestUpdate,
    OnboardingRecordCreate,
    OnboardingRecordUpdate,
    PayrollRecordCreate,
    PayrollRecordUpdate,
    PerformanceReviewCreate,
    PerformanceReviewUpdate,
    PositionCreate,
    PositionUpdate,
    TrainingRecordCreate,
    TrainingRecordUpdate,
    EmployeeBenefitCreate,
    EmployeeBenefitUpdate,
)


class EmployeeCRUD(CRUDBase[Employee, EmployeeCreate, EmployeeUpdate]):
    """CRUD operations for Employee management."""

    def __init__(self, db: Session):
        super().__init__(Employee)
        self.db = db

    def create_employee(
        self, obj_in: EmployeeCreate, created_by: str
    ) -> Employee:
        """Create a new employee with auto-generated employee number."""
        # Generate employee number if not provided
        if not obj_in.employee_number:
            obj_in.employee_number = self._generate_employee_number(obj_in.organization_id)
        
        # Set initial status based on hire date and employment type
        today = date.today()
        if obj_in.hire_date > today:
            initial_status = EmployeeStatus.INACTIVE
        elif obj_in.employment_type == EmploymentType.INTERN:
            initial_status = EmployeeStatus.PROBATION
        else:
            initial_status = EmployeeStatus.ACTIVE
        
        db_obj = Employee(
            **obj_in.dict(),
            employee_status=initial_status,
            created_by=created_by,
        )
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        
        return db_obj

    def get_by_employee_number(
        self, employee_number: str, organization_id: str
    ) -> Optional[Employee]:
        """Get employee by employee number within organization."""
        return (
            self.db.query(Employee)
            .filter(
                and_(
                    Employee.employee_number == employee_number,
                    Employee.organization_id == organization_id,
                )
            )
            .first()
        )

    def get_employees_by_manager(
        self, manager_id: str, include_indirect: bool = False
    ) -> List[Employee]:
        """Get employees reporting to a specific manager."""
        direct_reports = (
            self.db.query(Employee)
            .filter(Employee.manager_id == manager_id)
            .filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            .all()
        )
        
        if not include_indirect:
            return direct_reports
        
        # Get indirect reports recursively
        all_reports = direct_reports.copy()
        for employee in direct_reports:
            indirect_reports = self.get_employees_by_manager(employee.id, True)
            all_reports.extend(indirect_reports)
        
        return all_reports

    def get_employees_by_department(
        self, department_id: str, active_only: bool = True
    ) -> List[Employee]:
        """Get employees in specific department."""
        query = self.db.query(Employee).filter(Employee.department_id == department_id)
        
        if active_only:
            query = query.filter(Employee.employee_status == EmployeeStatus.ACTIVE)
        
        return query.all()

    def get_employee_org_chart(self, organization_id: str) -> List[Dict[str, Any]]:
        """Generate organizational chart data."""
        employees = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            .all()
        )
        
        org_chart = []
        for emp in employees:
            org_chart.append({
                "id": emp.id,
                "name": f"{emp.first_name} {emp.last_name}",
                "title": emp.job_title,
                "manager_id": emp.manager_id,
                "department_id": emp.department_id,
                "employee_number": emp.employee_number,
            })
        
        return org_chart

    def terminate_employee(
        self, employee_id: str, termination_date: date, 
        termination_reason: str, terminated_by: str
    ) -> Employee:
        """Terminate employee and update status."""
        employee = self.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        employee.employee_status = EmployeeStatus.TERMINATED
        employee.termination_date = termination_date
        employee.termination_reason = termination_reason
        employee.is_active = False
        employee.updated_by = terminated_by
        
        # Update any direct reports to remove manager
        direct_reports = self.get_employees_by_manager(employee_id)
        for report in direct_reports:
            report.manager_id = employee.manager_id  # Move to terminated employee's manager
        
        self.db.commit()
        return employee

    def calculate_employee_tenure(self, employee_id: str) -> Dict[str, Any]:
        """Calculate employee tenure and service metrics."""
        employee = self.get(employee_id)
        if not employee:
            raise ValueError("Employee not found")
        
        today = date.today()
        tenure_days = (today - employee.hire_date).days
        tenure_years = tenure_days / 365.25
        tenure_months = tenure_days / 30.44
        
        # Calculate service milestones
        milestones = []
        if tenure_years >= 1:
            milestones.append(f"{int(tenure_years)} year(s)")
        if tenure_years >= 5:
            milestones.append("5+ years")
        if tenure_years >= 10:
            milestones.append("10+ years veteran")
        
        return {
            "employee_id": employee_id,
            "hire_date": employee.hire_date,
            "tenure_days": tenure_days,
            "tenure_months": round(tenure_months, 1),
            "tenure_years": round(tenure_years, 2),
            "service_milestones": milestones,
            "is_probationary": employee.employee_status == EmployeeStatus.PROBATION,
            "probation_end_date": employee.probation_end_date,
        }

    def _generate_employee_number(self, organization_id: str) -> str:
        """Generate next employee number for organization."""
        # Get highest existing employee number
        highest = (
            self.db.query(Employee.employee_number)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.employee_number.regexp_match(r'^EMP\d+$'))
            .order_by(desc(Employee.employee_number))
            .first()
        )
        
        if highest:
            try:
                next_num = int(highest[0][3:]) + 1
                return f"EMP{next_num:06d}"
            except ValueError:
                pass
        
        return "EMP000001"


class PayrollCRUD(CRUDBase[PayrollRecord, PayrollRecordCreate, PayrollRecordUpdate]):
    """CRUD operations for Payroll processing."""

    def __init__(self, db: Session):
        super().__init__(PayrollRecord)
        self.db = db

    def calculate_payroll(
        self, employee_id: str, pay_period_start: date, pay_period_end: date,
        regular_hours: Decimal = None, overtime_hours: Decimal = None
    ) -> PayrollRecord:
        """Calculate payroll for employee for specified period."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
        
        # Calculate pay date (typically end of pay period + processing days)
        pay_date = pay_period_end + timedelta(days=3)
        
        # Use provided hours or default based on employment type
        if regular_hours is None:
            days_in_period = (pay_period_end - pay_period_start).days + 1
            if employee.employment_type == EmploymentType.FULL_TIME:
                regular_hours = Decimal(str(days_in_period * 8))  # 8 hours per day
            else:
                regular_hours = Decimal("0")
        
        if overtime_hours is None:
            overtime_hours = Decimal("0")
        
        # Calculate rates
        regular_rate = employee.hourly_rate or (employee.base_salary / 2080 if employee.base_salary else Decimal("0"))
        overtime_rate = regular_rate * Decimal("1.5")
        
        # Calculate gross pay
        regular_pay = regular_hours * regular_rate
        overtime_pay = overtime_hours * overtime_rate
        gross_pay = regular_pay + overtime_pay
        
        # Calculate taxable income (gross pay - pre-tax deductions)
        health_insurance = gross_pay * Decimal("0.08")  # Example: 8% for health insurance
        retirement_contribution = gross_pay * Decimal("0.05")  # Example: 5% 401k contribution
        taxable_income = gross_pay - health_insurance - retirement_contribution
        
        # Calculate tax withholdings (simplified calculation)
        federal_tax = taxable_income * Decimal("0.22")  # Example: 22% federal rate
        social_security = taxable_income * Decimal("0.062")  # 6.2% social security
        medicare_tax = taxable_income * Decimal("0.0145")  # 1.45% medicare
        total_taxes = federal_tax + social_security + medicare_tax
        
        # Calculate net pay
        net_pay = gross_pay - health_insurance - retirement_contribution - total_taxes
        
        # Get year-to-date totals
        ytd_totals = self._calculate_ytd_totals(employee_id, pay_period_end.year)
        
        payroll_record = PayrollRecord(
            employee_id=employee_id,
            organization_id=employee.organization_id,
            pay_period_start=pay_period_start,
            pay_period_end=pay_period_end,
            pay_date=pay_date,
            regular_hours=regular_hours,
            regular_rate=regular_rate,
            regular_pay=regular_pay,
            overtime_hours=overtime_hours,
            overtime_rate=overtime_rate,
            overtime_pay=overtime_pay,
            gross_pay=gross_pay,
            health_insurance_employee=health_insurance,
            retirement_contribution_employee=retirement_contribution,
            taxable_income=taxable_income,
            federal_income_tax=federal_tax,
            social_security_tax=social_security,
            medicare_tax=medicare_tax,
            net_pay=net_pay,
            ytd_gross_pay=ytd_totals["gross_pay"] + gross_pay,
            ytd_tax_withheld=ytd_totals["tax_withheld"] + total_taxes,
            ytd_net_pay=ytd_totals["net_pay"] + net_pay,
        )
        
        self.db.add(payroll_record)
        self.db.commit()
        self.db.refresh(payroll_record)
        
        return payroll_record

    def process_payroll_batch(
        self, organization_id: str, pay_period_start: date, 
        pay_period_end: date, processed_by: str
    ) -> List[PayrollRecord]:
        """Process payroll for all active employees in organization."""
        active_employees = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            .all()
        )
        
        payroll_records = []
        for employee in active_employees:
            try:
                payroll_record = self.calculate_payroll(
                    employee.id, pay_period_start, pay_period_end
                )
                payroll_record.processed_by = processed_by
                payroll_record.processed_date = datetime.utcnow()
                payroll_record.is_processed = True
                payroll_records.append(payroll_record)
            except Exception as e:
                # Log error but continue processing other employees
                print(f"Error processing payroll for employee {employee.employee_number}: {str(e)}")
                continue
        
        self.db.commit()
        return payroll_records

    def get_payroll_summary(
        self, organization_id: str, year: int, month: Optional[int] = None
    ) -> Dict[str, Any]:
        """Generate payroll summary for organization."""
        query = (
            self.db.query(PayrollRecord)
            .filter(PayrollRecord.organization_id == organization_id)
            .filter(func.extract('year', PayrollRecord.pay_period_end) == year)
        )
        
        if month:
            query = query.filter(func.extract('month', PayrollRecord.pay_period_end) == month)
        
        records = query.all()
        
        total_gross_pay = sum(record.gross_pay for record in records)
        total_net_pay = sum(record.net_pay for record in records)
        total_taxes = sum(
            (record.federal_income_tax or 0) + 
            (record.social_security_tax or 0) + 
            (record.medicare_tax or 0)
            for record in records
        )
        
        return {
            "organization_id": organization_id,
            "period": f"{year}-{month:02d}" if month else str(year),
            "total_employees_paid": len(set(record.employee_id for record in records)),
            "total_payroll_records": len(records),
            "total_gross_pay": float(total_gross_pay),
            "total_net_pay": float(total_net_pay),
            "total_taxes_withheld": float(total_taxes),
            "average_gross_pay": float(total_gross_pay / len(records)) if records else 0,
            "average_net_pay": float(total_net_pay / len(records)) if records else 0,
        }

    def _calculate_ytd_totals(self, employee_id: str, year: int) -> Dict[str, Decimal]:
        """Calculate year-to-date totals for employee."""
        ytd_records = (
            self.db.query(PayrollRecord)
            .filter(PayrollRecord.employee_id == employee_id)
            .filter(func.extract('year', PayrollRecord.pay_period_end) == year)
            .all()
        )
        
        return {
            "gross_pay": sum(record.gross_pay for record in ytd_records),
            "net_pay": sum(record.net_pay for record in ytd_records),
            "tax_withheld": sum(
                (record.federal_income_tax or 0) + 
                (record.social_security_tax or 0) + 
                (record.medicare_tax or 0)
                for record in ytd_records
            ),
        }


class LeaveCRUD(CRUDBase[LeaveRequest, LeaveRequestCreate, LeaveRequestUpdate]):
    """CRUD operations for Leave management."""

    def __init__(self, db: Session):
        super().__init__(LeaveRequest)
        self.db = db

    def create_leave_request(
        self, obj_in: LeaveRequestCreate, requested_by: str
    ) -> LeaveRequest:
        """Create leave request with automatic calculations."""
        # Calculate total days
        total_days = (obj_in.end_date - obj_in.start_date).days + 1
        
        # Get employee's current leave balance
        employee = self.db.query(Employee).filter(Employee.id == obj_in.employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
        
        current_balance = self._get_leave_balance(obj_in.employee_id, obj_in.leave_type)
        
        # Check if employee has sufficient balance (for paid leave types)
        if obj_in.leave_type in [LeaveType.ANNUAL, LeaveType.SICK] and current_balance < total_days:
            raise ValueError(f"Insufficient leave balance. Current balance: {current_balance} days")
        
        db_obj = LeaveRequest(
            **obj_in.dict(),
            total_days=total_days,
            balance_before=current_balance,
            balance_after=current_balance - total_days if obj_in.leave_type in [LeaveType.ANNUAL, LeaveType.SICK] else current_balance,
            requested_date=datetime.utcnow(),
        )
        
        self.db.add(db_obj)
        self.db.commit()
        self.db.refresh(db_obj)
        
        return db_obj

    def approve_leave_request(
        self, leave_request_id: str, approved_by: str, notes: str = ""
    ) -> LeaveRequest:
        """Approve leave request."""
        leave_request = self.get(leave_request_id)
        if not leave_request:
            raise ValueError("Leave request not found")
        
        if leave_request.status != LeaveStatus.PENDING:
            raise ValueError("Leave request is not in pending status")
        
        leave_request.status = LeaveStatus.APPROVED
        leave_request.approved_by = approved_by
        leave_request.approved_date = datetime.utcnow()
        leave_request.approval_notes = notes
        
        self.db.commit()
        return leave_request

    def get_employee_leave_calendar(
        self, employee_id: str, year: int
    ) -> List[Dict[str, Any]]:
        """Get employee's leave calendar for specified year."""
        leave_requests = (
            self.db.query(LeaveRequest)
            .filter(LeaveRequest.employee_id == employee_id)
            .filter(LeaveRequest.status == LeaveStatus.APPROVED)
            .filter(
                or_(
                    func.extract('year', LeaveRequest.start_date) == year,
                    func.extract('year', LeaveRequest.end_date) == year,
                )
            )
            .order_by(LeaveRequest.start_date)
            .all()
        )
        
        calendar_events = []
        for leave in leave_requests:
            calendar_events.append({
                "id": leave.id,
                "title": f"{leave.leave_type.value.title()} Leave",
                "start_date": leave.start_date,
                "end_date": leave.end_date,
                "total_days": leave.total_days,
                "leave_type": leave.leave_type.value,
                "is_paid": leave.is_paid,
                "status": leave.status.value,
            })
        
        return calendar_events

    def get_leave_balance_summary(
        self, employee_id: str
    ) -> Dict[str, Any]:
        """Get comprehensive leave balance summary for employee."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
        
        current_year = date.today().year
        balances = {}
        
        # Calculate balances for each leave type
        for leave_type in LeaveType:
            current_balance = self._get_leave_balance(employee_id, leave_type)
            accrued_this_year = self._calculate_accrued_leave(employee, leave_type, current_year)
            used_this_year = self._get_leave_used(employee_id, leave_type, current_year)
            
            balances[leave_type.value] = {
                "current_balance": current_balance,
                "accrued_this_year": accrued_this_year,
                "used_this_year": used_this_year,
                "accrual_rate": self._get_accrual_rate(employee, leave_type),
            }
        
        return {
            "employee_id": employee_id,
            "as_of_date": date.today(),
            "leave_balances": balances,
        }

    def _get_leave_balance(self, employee_id: str, leave_type: LeaveType) -> Decimal:
        """Calculate current leave balance for employee and leave type."""
        # This is a simplified calculation - in practice, you'd track accruals and usage
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            return Decimal("0")
        
        # Calculate tenure-based accrual
        tenure_years = (date.today() - employee.hire_date).days / 365.25
        
        if leave_type == LeaveType.ANNUAL:
            # Example: 20 days per year for employees with 1+ years
            annual_accrual = Decimal("20") if tenure_years >= 1 else Decimal("10")
        elif leave_type == LeaveType.SICK:
            # Example: 10 sick days per year
            annual_accrual = Decimal("10")
        else:
            # Other leave types don't accrue
            return Decimal("0")
        
        # Calculate used leave this year
        used_this_year = self._get_leave_used(employee_id, leave_type, date.today().year)
        
        return annual_accrual - used_this_year

    def _get_leave_used(self, employee_id: str, leave_type: LeaveType, year: int) -> Decimal:
        """Calculate total leave used by type and year."""
        used_leave = (
            self.db.query(func.sum(LeaveRequest.total_days))
            .filter(LeaveRequest.employee_id == employee_id)
            .filter(LeaveRequest.leave_type == leave_type)
            .filter(LeaveRequest.status == LeaveStatus.APPROVED)
            .filter(func.extract('year', LeaveRequest.start_date) == year)
            .scalar()
        )
        
        return Decimal(str(used_leave)) if used_leave else Decimal("0")

    def _calculate_accrued_leave(
        self, employee: Employee, leave_type: LeaveType, year: int
    ) -> Decimal:
        """Calculate leave accrued for employee by type and year."""
        # Simplified accrual calculation
        if leave_type == LeaveType.ANNUAL:
            return Decimal("20")  # 20 days per year
        elif leave_type == LeaveType.SICK:
            return Decimal("10")  # 10 sick days per year
        else:
            return Decimal("0")

    def _get_accrual_rate(self, employee: Employee, leave_type: LeaveType) -> str:
        """Get leave accrual rate description."""
        if leave_type == LeaveType.ANNUAL:
            return "20 days per year"
        elif leave_type == LeaveType.SICK:
            return "10 days per year"
        else:
            return "N/A"


class PerformanceCRUD(CRUDBase[PerformanceReview, PerformanceReviewCreate, PerformanceReviewUpdate]):
    """CRUD operations for Performance management."""

    def __init__(self, db: Session):
        super().__init__(PerformanceReview)
        self.db = db

    def create_performance_review_cycle(
        self, organization_id: str, review_period_start: date,
        review_period_end: date, created_by: str
    ) -> List[PerformanceReview]:
        """Create performance reviews for all eligible employees."""
        eligible_employees = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            .filter(Employee.hire_date <= review_period_start)  # Must be hired before review period
            .all()
        )
        
        reviews = []
        for employee in eligible_employees:
            # Skip if employee already has a review for this period
            existing_review = (
                self.db.query(PerformanceReview)
                .filter(PerformanceReview.employee_id == employee.id)
                .filter(PerformanceReview.review_period_start == review_period_start)
                .filter(PerformanceReview.review_period_end == review_period_end)
                .first()
            )
            
            if existing_review:
                continue
            
            # Assign reviewer (typically the manager)
            reviewer_id = employee.manager_id or created_by
            
            review = PerformanceReview(
                employee_id=employee.id,
                organization_id=organization_id,
                review_period_start=review_period_start,
                review_period_end=review_period_end,
                reviewer_id=reviewer_id,
                review_type="annual",
            )
            
            self.db.add(review)
            reviews.append(review)
        
        self.db.commit()
        for review in reviews:
            self.db.refresh(review)
        
        return reviews

    def calculate_overall_score(self, review_id: str) -> PerformanceReview:
        """Calculate overall performance score from individual ratings."""
        review = self.get(review_id)
        if not review:
            raise ValueError("Performance review not found")
        
        # Define weights for different performance areas
        weights = {
            "job_knowledge": 0.20,
            "quality_of_work": 0.25,
            "productivity": 0.20,
            "communication": 0.15,
            "teamwork": 0.10,
            "leadership": 0.10,
        }
        
        # Convert ratings to numeric scores (1-5 scale)
        rating_to_score = {
            PerformanceRating.OUTSTANDING: 5.0,
            PerformanceRating.EXCEEDS_EXPECTATIONS: 4.0,
            PerformanceRating.MEETS_EXPECTATIONS: 3.0,
            PerformanceRating.NEEDS_IMPROVEMENT: 2.0,
            PerformanceRating.UNSATISFACTORY: 1.0,
        }
        
        weighted_scores = []
        
        if review.job_knowledge_rating:
            score = rating_to_score[review.job_knowledge_rating]
            weighted_scores.append(score * weights["job_knowledge"])
            review.job_knowledge_score = Decimal(str(score))
        
        if review.quality_of_work_rating:
            score = rating_to_score[review.quality_of_work_rating]
            weighted_scores.append(score * weights["quality_of_work"])
            review.quality_of_work_score = Decimal(str(score))
        
        if review.productivity_rating:
            score = rating_to_score[review.productivity_rating]
            weighted_scores.append(score * weights["productivity"])
            review.productivity_score = Decimal(str(score))
        
        if review.communication_rating:
            score = rating_to_score[review.communication_rating]
            weighted_scores.append(score * weights["communication"])
            review.communication_score = Decimal(str(score))
        
        if review.teamwork_rating:
            score = rating_to_score[review.teamwork_rating]
            weighted_scores.append(score * weights["teamwork"])
            review.teamwork_score = Decimal(str(score))
        
        if review.leadership_rating:
            score = rating_to_score[review.leadership_rating]
            weighted_scores.append(score * weights["leadership"])
            review.leadership_score = Decimal(str(score))
        
        # Calculate overall score
        if weighted_scores:
            overall_score = sum(weighted_scores)
            review.overall_score = Decimal(str(round(overall_score, 2)))
            
            # Determine overall rating based on score
            if overall_score >= 4.5:
                review.overall_rating = PerformanceRating.OUTSTANDING
            elif overall_score >= 3.5:
                review.overall_rating = PerformanceRating.EXCEEDS_EXPECTATIONS
            elif overall_score >= 2.5:
                review.overall_rating = PerformanceRating.MEETS_EXPECTATIONS
            elif overall_score >= 1.5:
                review.overall_rating = PerformanceRating.NEEDS_IMPROVEMENT
            else:
                review.overall_rating = PerformanceRating.UNSATISFACTORY
        
        self.db.commit()
        return review

    def get_performance_trends(
        self, employee_id: str, years: int = 3
    ) -> Dict[str, Any]:
        """Get performance trends for employee over specified years."""
        cutoff_date = date.today() - timedelta(days=years * 365)
        
        reviews = (
            self.db.query(PerformanceReview)
            .filter(PerformanceReview.employee_id == employee_id)
            .filter(PerformanceReview.review_period_end >= cutoff_date)
            .filter(PerformanceReview.status == "completed")
            .order_by(PerformanceReview.review_period_end)
            .all()
        )
        
        trend_data = []
        for review in reviews:
            trend_data.append({
                "review_date": review.review_period_end,
                "overall_score": float(review.overall_score) if review.overall_score else None,
                "overall_rating": review.overall_rating.value if review.overall_rating else None,
                "review_type": review.review_type,
                "salary_increase_recommended": review.salary_increase_recommended,
                "promotion_readiness": review.promotion_readiness,
            })
        
        # Calculate trend direction
        trend_direction = "stable"
        if len(trend_data) >= 2:
            recent_scores = [t["overall_score"] for t in trend_data[-2:] if t["overall_score"]]
            if len(recent_scores) == 2:
                if recent_scores[1] > recent_scores[0]:
                    trend_direction = "improving"
                elif recent_scores[1] < recent_scores[0]:
                    trend_direction = "declining"
        
        return {
            "employee_id": employee_id,
            "trend_period_years": years,
            "total_reviews": len(reviews),
            "trend_direction": trend_direction,
            "average_score": sum(t["overall_score"] for t in trend_data if t["overall_score"]) / len([t for t in trend_data if t["overall_score"]]) if trend_data else 0,
            "performance_history": trend_data,
        }


class TrainingCRUD(CRUDBase[TrainingRecord, TrainingRecordCreate, TrainingRecordUpdate]):
    """CRUD operations for Training management."""

    def __init__(self, db: Session):
        super().__init__(TrainingRecord)
        self.db = db

    def enroll_employee_in_training(
        self, employee_id: str, training_data: TrainingRecordCreate
    ) -> TrainingRecord:
        """Enroll employee in training program."""
        employee = self.db.query(Employee).filter(Employee.id == employee_id).first()
        if not employee:
            raise ValueError("Employee not found")
        
        # Check for scheduling conflicts
        conflicts = self._check_training_conflicts(employee_id, training_data.start_date, training_data.end_date)
        if conflicts:
            raise ValueError(f"Training conflicts with existing training: {conflicts}")
        
        training_record = TrainingRecord(
            employee_id=employee_id,
            organization_id=employee.organization_id,
            **training_data.dict()
        )
        
        self.db.add(training_record)
        self.db.commit()
        self.db.refresh(training_record)
        
        return training_record

    def complete_training(
        self, training_id: str, completion_data: Dict[str, Any]
    ) -> TrainingRecord:
        """Mark training as completed with assessment results."""
        training = self.get(training_id)
        if not training:
            raise ValueError("Training record not found")
        
        training.status = TrainingStatus.COMPLETED
        training.completion_date = datetime.utcnow()
        training.completion_percentage = Decimal("100")
        
        if "assessment_score" in completion_data:
            training.assessment_score = Decimal(str(completion_data["assessment_score"]))
            
            # Check if certification was earned
            if training.passing_score and training.assessment_score >= training.passing_score:
                training.certification_earned = True
                training.certificate_number = completion_data.get("certificate_number")
                training.certification_expiry_date = completion_data.get("certification_expiry_date")
        
        # Record feedback
        training.employee_satisfaction_rating = completion_data.get("satisfaction_rating")
        training.knowledge_gained_rating = completion_data.get("knowledge_rating")
        training.applicability_rating = completion_data.get("applicability_rating")
        training.employee_feedback = completion_data.get("employee_feedback")
        
        self.db.commit()
        return training

    def get_employee_training_history(
        self, employee_id: str, include_certifications: bool = True
    ) -> Dict[str, Any]:
        """Get comprehensive training history for employee."""
        training_records = (
            self.db.query(TrainingRecord)
            .filter(TrainingRecord.employee_id == employee_id)
            .order_by(desc(TrainingRecord.start_date))
            .all()
        )
        
        completed_trainings = [t for t in training_records if t.status == TrainingStatus.COMPLETED]
        active_certifications = [
            t for t in completed_trainings 
            if t.certification_earned and (
                not t.certification_expiry_date or 
                t.certification_expiry_date > date.today()
            )
        ]
        
        total_hours = sum(
            t.duration_hours for t in completed_trainings 
            if t.duration_hours
        )
        
        training_by_category = {}
        for training in training_records:
            category = training.training_category or "Other"
            if category not in training_by_category:
                training_by_category[category] = []
            training_by_category[category].append({
                "id": training.id,
                "title": training.training_title,
                "status": training.status.value,
                "completion_date": training.completion_date,
                "duration_hours": float(training.duration_hours) if training.duration_hours else 0,
                "certification_earned": training.certification_earned,
            })
        
        result = {
            "employee_id": employee_id,
            "total_trainings": len(training_records),
            "completed_trainings": len(completed_trainings),
            "total_training_hours": float(total_hours),
            "active_certifications": len(active_certifications),
            "training_by_category": training_by_category,
        }
        
        if include_certifications:
            result["certifications"] = [
                {
                    "training_title": cert.training_title,
                    "certificate_number": cert.certificate_number,
                    "earned_date": cert.completion_date,
                    "expiry_date": cert.certification_expiry_date,
                }
                for cert in active_certifications
            ]
        
        return result

    def get_training_compliance_report(
        self, organization_id: str, training_category: str = None
    ) -> Dict[str, Any]:
        """Generate training compliance report for organization."""
        # Get all active employees
        employees = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            .all()
        )
        
        # Get training records
        query = (
            self.db.query(TrainingRecord)
            .filter(TrainingRecord.organization_id == organization_id)
        )
        
        if training_category:
            query = query.filter(TrainingRecord.training_category == training_category)
        
        training_records = query.all()
        
        # Calculate compliance metrics
        total_employees = len(employees)
        employees_with_training = len(set(t.employee_id for t in training_records))
        completed_trainings = len([t for t in training_records if t.status == TrainingStatus.COMPLETED])
        
        compliance_rate = (employees_with_training / total_employees * 100) if total_employees > 0 else 0
        completion_rate = (completed_trainings / len(training_records) * 100) if training_records else 0
        
        return {
            "organization_id": organization_id,
            "training_category": training_category,
            "report_date": date.today(),
            "total_employees": total_employees,
            "employees_with_training": employees_with_training,
            "compliance_rate": round(compliance_rate, 2),
            "total_training_records": len(training_records),
            "completed_trainings": completed_trainings,
            "completion_rate": round(completion_rate, 2),
            "average_training_hours": sum(t.duration_hours for t in training_records if t.duration_hours) / len(training_records) if training_records else 0,
        }

    def _check_training_conflicts(
        self, employee_id: str, start_date: datetime, end_date: datetime
    ) -> List[str]:
        """Check for training scheduling conflicts."""
        conflicts = (
            self.db.query(TrainingRecord)
            .filter(TrainingRecord.employee_id == employee_id)
            .filter(TrainingRecord.status.in_([TrainingStatus.SCHEDULED, TrainingStatus.IN_PROGRESS]))
            .filter(
                or_(
                    and_(TrainingRecord.start_date <= start_date, TrainingRecord.end_date >= start_date),
                    and_(TrainingRecord.start_date <= end_date, TrainingRecord.end_date >= end_date),
                    and_(TrainingRecord.start_date >= start_date, TrainingRecord.end_date <= end_date),
                )
            )
            .all()
        )
        
        return [f"{c.training_title} ({c.start_date} - {c.end_date})" for c in conflicts]


class HRAnalyticsCRUD(CRUDBase[HRAnalytics, None, None]):
    """CRUD operations for HR Analytics."""

    def __init__(self, db: Session):
        super().__init__(HRAnalytics)
        self.db = db

    def calculate_hr_metrics(
        self, organization_id: str, period_start: date, period_end: date,
        calculated_by: str
    ) -> HRAnalytics:
        """Calculate comprehensive HR metrics for specified period."""
        
        # Get employee counts
        total_employees = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.hire_date <= period_end)
            .filter(
                or_(
                    Employee.termination_date.is_(None),
                    Employee.termination_date > period_start
                )
            )
            .count()
        )
        
        active_employees = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            .filter(Employee.hire_date <= period_end)
            .count()
        )
        
        # Calculate hiring metrics
        new_hires = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.hire_date >= period_start)
            .filter(Employee.hire_date <= period_end)
            .count()
        )
        
        # Calculate turnover metrics
        terminations = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.termination_date >= period_start)
            .filter(Employee.termination_date <= period_end)
            .count()
        )
        
        voluntary_terminations = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.termination_date >= period_start)
            .filter(Employee.termination_date <= period_end)
            .filter(Employee.termination_reason.like('%voluntary%'))
            .count()
        )
        
        # Calculate rates
        turnover_rate = (terminations / active_employees * 100) if active_employees > 0 else 0
        voluntary_turnover_rate = (voluntary_terminations / active_employees * 100) if active_employees > 0 else 0
        retention_rate = 100 - turnover_rate
        
        # Get performance metrics
        performance_reviews = (
            self.db.query(PerformanceReview)
            .filter(PerformanceReview.organization_id == organization_id)
            .filter(PerformanceReview.review_period_end >= period_start)
            .filter(PerformanceReview.review_period_end <= period_end)
            .all()
        )
        
        completed_reviews = [r for r in performance_reviews if r.status == "completed"]
        review_completion_rate = (len(completed_reviews) / len(performance_reviews) * 100) if performance_reviews else 0
        
        # Get training metrics
        training_records = (
            self.db.query(TrainingRecord)
            .filter(TrainingRecord.organization_id == organization_id)
            .filter(TrainingRecord.start_date >= period_start)
            .filter(TrainingRecord.start_date <= period_end)
            .all()
        )
        
        completed_trainings = [t for t in training_records if t.status == TrainingStatus.COMPLETED]
        training_completion_rate = (len(completed_trainings) / len(training_records) * 100) if training_records else 0
        
        # Get payroll metrics
        payroll_records = (
            self.db.query(PayrollRecord)
            .filter(PayrollRecord.organization_id == organization_id)
            .filter(PayrollRecord.pay_period_end >= period_start)
            .filter(PayrollRecord.pay_period_end <= period_end)
            .all()
        )
        
        total_payroll_cost = sum(record.gross_pay for record in payroll_records)
        average_salary = total_payroll_cost / len(payroll_records) if payroll_records else 0
        
        analytics = HRAnalytics(
            organization_id=organization_id,
            period_start=period_start,
            period_end=period_end,
            total_employees=total_employees,
            active_employees=active_employees,
            new_hires=new_hires,
            total_terminations=terminations,
            voluntary_terminations=voluntary_terminations,
            turnover_rate=Decimal(str(round(turnover_rate, 2))),
            voluntary_turnover_rate=Decimal(str(round(voluntary_turnover_rate, 2))),
            retention_rate=Decimal(str(round(retention_rate, 2))),
            performance_review_completion_rate=Decimal(str(round(review_completion_rate, 2))),
            training_completion_rate=Decimal(str(round(training_completion_rate, 2))),
            average_salary=Decimal(str(round(average_salary, 2))),
            payroll_cost_total=Decimal(str(total_payroll_cost)),
            calculated_date=datetime.utcnow(),
            calculated_by=calculated_by,
        )
        
        self.db.add(analytics)
        self.db.commit()
        self.db.refresh(analytics)
        
        return analytics

    def get_hr_dashboard_metrics(
        self, organization_id: str, as_of_date: date = None
    ) -> Dict[str, Any]:
        """Get key HR metrics for dashboard display."""
        if not as_of_date:
            as_of_date = date.today()
        
        # Get latest analytics record
        latest_analytics = (
            self.db.query(HRAnalytics)
            .filter(HRAnalytics.organization_id == organization_id)
            .filter(HRAnalytics.period_end <= as_of_date)
            .order_by(desc(HRAnalytics.period_end))
            .first()
        )
        
        if not latest_analytics:
            return {"message": "No HR analytics data available"}
        
        # Get current employee counts
        current_active = (
            self.db.query(Employee)
            .filter(Employee.organization_id == organization_id)
            .filter(Employee.employee_status == EmployeeStatus.ACTIVE)
            .count()
        )
        
        # Get pending leave requests
        pending_leave = (
            self.db.query(LeaveRequest)
            .filter(LeaveRequest.organization_id == organization_id)
            .filter(LeaveRequest.status == LeaveStatus.PENDING)
            .count()
        )
        
        # Get upcoming performance reviews
        upcoming_reviews = (
            self.db.query(PerformanceReview)
            .filter(PerformanceReview.organization_id == organization_id)
            .filter(PerformanceReview.status == "draft")
            .count()
        )
        
        return {
            "organization_id": organization_id,
            "as_of_date": as_of_date,
            "current_active_employees": current_active,
            "turnover_rate": float(latest_analytics.turnover_rate),
            "retention_rate": float(latest_analytics.retention_rate),
            "new_hires_this_period": latest_analytics.new_hires,
            "performance_review_completion_rate": float(latest_analytics.performance_review_completion_rate),
            "training_completion_rate": float(latest_analytics.training_completion_rate),
            "average_salary": float(latest_analytics.average_salary),
            "pending_leave_requests": pending_leave,
            "upcoming_performance_reviews": upcoming_reviews,
            "last_analytics_update": latest_analytics.calculated_date,
        }