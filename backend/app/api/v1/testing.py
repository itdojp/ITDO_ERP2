"""
CC02 v55.0 Testing Management API
Comprehensive Test Automation and Quality Assurance Management
Day 7 of 7-day intensive backend development
"""

import asyncio
from datetime import date, datetime, timedelta
from typing import Any, Dict, List, Optional
from uuid import UUID, uuid4

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Path,
    Query,
    status,
)
from pydantic import BaseModel, Field
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.testing import TestCase, TestExecution, TestResult, TestSuite
from app.models.user import User
from app.services.test_automation_engine import (
    TestEnvironment,
    TestPriority,
    TestStatus,
    TestType,
    test_automation_engine,
)

router = APIRouter(prefix="/testing", tags=["testing"])


# Request/Response Models
class TestCaseRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    test_type: TestType
    priority: TestPriority = TestPriority.MEDIUM
    test_environment: TestEnvironment = TestEnvironment.TESTING
    test_data: Dict[str, Any] = Field(default_factory=dict)
    expected_results: Dict[str, Any] = Field(default_factory=dict)
    timeout_seconds: int = Field(default=30, ge=1, le=3600)
    retry_count: int = Field(default=0, ge=0, le=5)
    tags: List[str] = Field(default_factory=list)


class TestCaseResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    test_type: TestType
    priority: TestPriority
    test_environment: TestEnvironment
    test_data: Dict[str, Any]
    expected_results: Dict[str, Any]
    timeout_seconds: int
    retry_count: int
    tags: List[str]
    execution_count: int
    last_execution: Optional[datetime]
    last_status: Optional[TestStatus]
    success_rate: float
    average_execution_time: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestSuiteRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    test_case_ids: List[UUID] = Field(default_factory=list)
    parallel_execution: bool = Field(default=False)
    fail_fast: bool = Field(default=False)
    timeout_seconds: int = Field(default=300, ge=1, le=7200)
    tags: List[str] = Field(default_factory=list)


class TestSuiteResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    test_case_count: int
    parallel_execution: bool
    fail_fast: bool
    timeout_seconds: int
    tags: List[str]
    execution_count: int
    last_execution: Optional[datetime]
    last_status: Optional[str]
    success_rate: float
    average_execution_time: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class TestExecutionRequest(BaseModel):
    test_suite_id: Optional[UUID] = None
    test_case_ids: Optional[List[UUID]] = None
    test_environment: TestEnvironment = TestEnvironment.TESTING
    parallel_execution: bool = Field(default=False)
    tags: Optional[List[str]] = None
    execution_notes: Optional[str] = Field(None, max_length=1000)


class TestExecutionResponse(BaseModel):
    id: UUID
    test_suite_id: Optional[UUID]
    test_suite_name: Optional[str]
    test_environment: TestEnvironment
    status: str
    total_tests: int
    passed_tests: int
    failed_tests: int
    skipped_tests: int
    error_tests: int
    execution_time: float
    coverage_percentage: float
    started_at: datetime
    completed_at: Optional[datetime]
    execution_notes: Optional[str]

    class Config:
        from_attributes = True


class TestResultResponse(BaseModel):
    id: UUID
    test_case_id: UUID
    test_case_name: str
    execution_id: UUID
    status: TestStatus
    execution_time: float
    assertions_passed: int
    assertions_failed: int
    error_message: Optional[str]
    stack_trace: Optional[str]
    output_logs: List[str]
    metadata: Dict[str, Any]
    executed_at: datetime

    class Config:
        from_attributes = True


class APITestRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    endpoint: str = Field(..., min_length=1, max_length=500)
    method: str = Field(..., regex="^(GET|POST|PUT|DELETE|PATCH)$")
    headers: Dict[str, str] = Field(default_factory=dict)
    request_data: Optional[Dict[str, Any]] = None
    expected_status_code: int = Field(default=200, ge=100, le=599)
    expected_response_schema: Optional[Dict[str, Any]] = None
    performance_threshold_ms: int = Field(default=2000, ge=1, le=30000)
    tags: List[str] = Field(default_factory=list)


class PerformanceTestRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    target_endpoint: str = Field(..., min_length=1, max_length=500)
    iterations: int = Field(default=100, ge=1, le=10000)
    concurrent_users: int = Field(default=1, ge=1, le=1000)
    max_execution_time_ms: int = Field(default=1000, ge=1, le=60000)
    max_memory_usage_mb: int = Field(default=100, ge=1, le=1000)
    tags: List[str] = Field(default_factory=list)


class TestPlanRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    test_suite_ids: List[UUID]
    schedule_expression: Optional[str] = Field(
        None, description="Cron expression for scheduled execution"
    )
    test_environment: TestEnvironment = TestEnvironment.TESTING
    quality_gates: Dict[str, Any] = Field(default_factory=dict)
    notification_settings: Dict[str, Any] = Field(default_factory=dict)


class TestPlanResponse(BaseModel):
    id: UUID
    name: str
    description: Optional[str]
    test_suite_count: int
    schedule_expression: Optional[str]
    test_environment: TestEnvironment
    quality_gates: Dict[str, Any]
    notification_settings: Dict[str, Any]
    execution_count: int
    last_execution: Optional[datetime]
    next_scheduled_execution: Optional[datetime]
    success_rate: float
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CoverageReportResponse(BaseModel):
    coverage_percentage: float
    lines_covered: int
    lines_total: int
    files_analyzed: int
    branches_covered: float
    generated_at: datetime
    details: Dict[str, float]

    class Config:
        from_attributes = True


# Test Case Management
@router.post(
    "/test-cases", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED
)
async def create_test_case(
    test_case: TestCaseRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new test case"""

    db_test_case = TestCase(
        id=uuid4(),
        name=test_case.name,
        description=test_case.description,
        test_type=test_case.test_type,
        priority=test_case.priority,
        test_environment=test_case.test_environment,
        test_data=test_case.test_data,
        expected_results=test_case.expected_results,
        timeout_seconds=test_case.timeout_seconds,
        retry_count=test_case.retry_count,
        tags=test_case.tags,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(db_test_case)
    await db.commit()
    await db.refresh(db_test_case)

    return TestCaseResponse(
        id=db_test_case.id,
        name=db_test_case.name,
        description=db_test_case.description,
        test_type=db_test_case.test_type,
        priority=db_test_case.priority,
        test_environment=db_test_case.test_environment,
        test_data=db_test_case.test_data,
        expected_results=db_test_case.expected_results,
        timeout_seconds=db_test_case.timeout_seconds,
        retry_count=db_test_case.retry_count,
        tags=db_test_case.tags,
        execution_count=0,
        last_execution=None,
        last_status=None,
        success_rate=0.0,
        average_execution_time=0.0,
        created_at=db_test_case.created_at,
        updated_at=db_test_case.updated_at,
    )


@router.get("/test-cases", response_model=List[TestCaseResponse])
async def list_test_cases(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    test_type: Optional[TestType] = Query(None),
    priority: Optional[TestPriority] = Query(None),
    test_environment: Optional[TestEnvironment] = Query(None),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List test cases"""

    query = select(TestCase)

    if test_type:
        query = query.where(TestCase.test_type == test_type)

    if priority:
        query = query.where(TestCase.priority == priority)

    if test_environment:
        query = query.where(TestCase.test_environment == test_environment)

    # TODO: Add tag filtering

    query = query.offset(skip).limit(limit).order_by(TestCase.created_at.desc())

    result = await db.execute(query)
    test_cases = result.scalars().all()

    return [
        TestCaseResponse(
            id=tc.id,
            name=tc.name,
            description=tc.description,
            test_type=tc.test_type,
            priority=tc.priority,
            test_environment=tc.test_environment,
            test_data=tc.test_data,
            expected_results=tc.expected_results,
            timeout_seconds=tc.timeout_seconds,
            retry_count=tc.retry_count,
            tags=tc.tags,
            execution_count=0,  # Would calculate from test results
            last_execution=None,  # Would get from test results
            last_status=None,  # Would get from test results
            success_rate=0.0,  # Would calculate from test results
            average_execution_time=0.0,  # Would calculate from test results
            created_at=tc.created_at,
            updated_at=tc.updated_at,
        )
        for tc in test_cases
    ]


@router.get("/test-cases/{test_case_id}", response_model=TestCaseResponse)
async def get_test_case(
    test_case_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get test case details"""

    test_case_result = await db.execute(
        select(TestCase).where(TestCase.id == test_case_id)
    )
    test_case = test_case_result.scalar_one_or_none()

    if not test_case:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test case not found"
        )

    # Get execution statistics
    execution_stats = await db.execute(
        select(
            func.count(TestResult.id).label("execution_count"),
            func.avg(TestResult.execution_time).label("avg_execution_time"),
            func.max(TestResult.executed_at).label("last_execution"),
        ).where(TestResult.test_case_id == test_case_id)
    )
    stats = execution_stats.first()

    # Get success rate
    success_count = await db.execute(
        select(func.count(TestResult.id)).where(
            and_(
                TestResult.test_case_id == test_case_id,
                TestResult.status == TestStatus.PASSED,
            )
        )
    )
    success_rate = (
        (success_count.scalar() / stats.execution_count * 100)
        if stats.execution_count > 0
        else 0.0
    )

    return TestCaseResponse(
        id=test_case.id,
        name=test_case.name,
        description=test_case.description,
        test_type=test_case.test_type,
        priority=test_case.priority,
        test_environment=test_case.test_environment,
        test_data=test_case.test_data,
        expected_results=test_case.expected_results,
        timeout_seconds=test_case.timeout_seconds,
        retry_count=test_case.retry_count,
        tags=test_case.tags,
        execution_count=stats.execution_count or 0,
        last_execution=stats.last_execution,
        last_status=None,  # Would get from latest test result
        success_rate=success_rate,
        average_execution_time=float(stats.avg_execution_time or 0),
        created_at=test_case.created_at,
        updated_at=test_case.updated_at,
    )


# Test Suite Management
@router.post(
    "/test-suites",
    response_model=TestSuiteResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_test_suite(
    test_suite: TestSuiteRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create a new test suite"""

    # Validate test case IDs
    if test_suite.test_case_ids:
        test_cases_result = await db.execute(
            select(TestCase.id).where(TestCase.id.in_(test_suite.test_case_ids))
        )
        existing_ids = {row[0] for row in test_cases_result.fetchall()}

        invalid_ids = set(test_suite.test_case_ids) - existing_ids
        if invalid_ids:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid test case IDs: {list(invalid_ids)}",
            )

    db_test_suite = TestSuite(
        id=uuid4(),
        name=test_suite.name,
        description=test_suite.description,
        test_case_ids=test_suite.test_case_ids,
        parallel_execution=test_suite.parallel_execution,
        fail_fast=test_suite.fail_fast,
        timeout_seconds=test_suite.timeout_seconds,
        tags=test_suite.tags,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(db_test_suite)
    await db.commit()
    await db.refresh(db_test_suite)

    return TestSuiteResponse(
        id=db_test_suite.id,
        name=db_test_suite.name,
        description=db_test_suite.description,
        test_case_count=len(test_suite.test_case_ids),
        parallel_execution=db_test_suite.parallel_execution,
        fail_fast=db_test_suite.fail_fast,
        timeout_seconds=db_test_suite.timeout_seconds,
        tags=db_test_suite.tags,
        execution_count=0,
        last_execution=None,
        last_status=None,
        success_rate=0.0,
        average_execution_time=0.0,
        created_at=db_test_suite.created_at,
        updated_at=db_test_suite.updated_at,
    )


@router.get("/test-suites", response_model=List[TestSuiteResponse])
async def list_test_suites(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    tags: Optional[str] = Query(None, description="Comma-separated list of tags"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List test suites"""

    query = select(TestSuite)

    # TODO: Add tag filtering

    query = query.offset(skip).limit(limit).order_by(TestSuite.created_at.desc())

    result = await db.execute(query)
    test_suites = result.scalars().all()

    return [
        TestSuiteResponse(
            id=ts.id,
            name=ts.name,
            description=ts.description,
            test_case_count=len(ts.test_case_ids or []),
            parallel_execution=ts.parallel_execution,
            fail_fast=ts.fail_fast,
            timeout_seconds=ts.timeout_seconds,
            tags=ts.tags,
            execution_count=0,  # Would calculate from executions
            last_execution=None,  # Would get from executions
            last_status=None,  # Would get from executions
            success_rate=0.0,  # Would calculate from executions
            average_execution_time=0.0,  # Would calculate from executions
            created_at=ts.created_at,
            updated_at=ts.updated_at,
        )
        for ts in test_suites
    ]


# Test Execution
@router.post(
    "/execute",
    response_model=TestExecutionResponse,
    status_code=status.HTTP_201_CREATED,
)
async def execute_tests(
    execution_request: TestExecutionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Execute tests"""

    execution_id = uuid4()

    # Create execution record
    db_execution = TestExecution(
        id=execution_id,
        test_suite_id=execution_request.test_suite_id,
        test_environment=execution_request.test_environment,
        status="running",
        parallel_execution=execution_request.parallel_execution,
        execution_notes=execution_request.execution_notes,
        started_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(db_execution)
    await db.commit()

    # Execute tests in background
    background_tasks.add_task(
        _execute_tests_background, execution_id, execution_request, db
    )

    return TestExecutionResponse(
        id=execution_id,
        test_suite_id=execution_request.test_suite_id,
        test_suite_name=None,  # Would get from test suite
        test_environment=execution_request.test_environment,
        status="running",
        total_tests=0,
        passed_tests=0,
        failed_tests=0,
        skipped_tests=0,
        error_tests=0,
        execution_time=0.0,
        coverage_percentage=0.0,
        started_at=datetime.utcnow(),
        completed_at=None,
        execution_notes=execution_request.execution_notes,
    )


async def _execute_tests_background(
    execution_id: UUID, execution_request: TestExecutionRequest, db: AsyncSession
):
    """Execute tests in background"""
    try:
        # In production, would execute actual tests using test automation engine
        await asyncio.sleep(5)  # Simulate test execution

        # Update execution status
        await db.execute(
            update(TestExecution)
            .where(TestExecution.id == execution_id)
            .values(
                status="completed",
                total_tests=10,
                passed_tests=8,
                failed_tests=2,
                execution_time=45.0,
                coverage_percentage=85.0,
                completed_at=datetime.utcnow(),
            )
        )
        await db.commit()

    except Exception as e:
        # Update execution with error status
        await db.execute(
            update(TestExecution)
            .where(TestExecution.id == execution_id)
            .values(
                status="failed", error_message=str(e), completed_at=datetime.utcnow()
            )
        )
        await db.commit()


@router.get("/executions", response_model=List[TestExecutionResponse])
async def list_test_executions(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    test_suite_id: Optional[UUID] = Query(None),
    test_environment: Optional[TestEnvironment] = Query(None),
    status: Optional[str] = Query(None),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """List test executions"""

    query = select(TestExecution, TestSuite.name.label("suite_name")).outerjoin(
        TestSuite, TestExecution.test_suite_id == TestSuite.id
    )

    if test_suite_id:
        query = query.where(TestExecution.test_suite_id == test_suite_id)

    if test_environment:
        query = query.where(TestExecution.test_environment == test_environment)

    if status:
        query = query.where(TestExecution.status == status)

    if date_from:
        query = query.where(TestExecution.started_at >= date_from)

    if date_to:
        query = query.where(TestExecution.started_at <= date_to)

    query = query.offset(skip).limit(limit).order_by(TestExecution.started_at.desc())

    result = await db.execute(query)
    executions = result.fetchall()

    return [
        TestExecutionResponse(
            id=execution.TestExecution.id,
            test_suite_id=execution.TestExecution.test_suite_id,
            test_suite_name=execution.suite_name,
            test_environment=execution.TestExecution.test_environment,
            status=execution.TestExecution.status,
            total_tests=execution.TestExecution.total_tests or 0,
            passed_tests=execution.TestExecution.passed_tests or 0,
            failed_tests=execution.TestExecution.failed_tests or 0,
            skipped_tests=execution.TestExecution.skipped_tests or 0,
            error_tests=execution.TestExecution.error_tests or 0,
            execution_time=execution.TestExecution.execution_time or 0.0,
            coverage_percentage=execution.TestExecution.coverage_percentage or 0.0,
            started_at=execution.TestExecution.started_at,
            completed_at=execution.TestExecution.completed_at,
            execution_notes=execution.TestExecution.execution_notes,
        )
        for execution in executions
    ]


@router.get("/executions/{execution_id}", response_model=TestExecutionResponse)
async def get_test_execution(
    execution_id: UUID = Path(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get test execution details"""

    execution_result = await db.execute(
        select(TestExecution, TestSuite.name.label("suite_name"))
        .outerjoin(TestSuite, TestExecution.test_suite_id == TestSuite.id)
        .where(TestExecution.id == execution_id)
    )
    execution_data = execution_result.first()

    if not execution_data:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Test execution not found"
        )

    execution = execution_data.TestExecution

    return TestExecutionResponse(
        id=execution.id,
        test_suite_id=execution.test_suite_id,
        test_suite_name=execution_data.suite_name,
        test_environment=execution.test_environment,
        status=execution.status,
        total_tests=execution.total_tests or 0,
        passed_tests=execution.passed_tests or 0,
        failed_tests=execution.failed_tests or 0,
        skipped_tests=execution.skipped_tests or 0,
        error_tests=execution.error_tests or 0,
        execution_time=execution.execution_time or 0.0,
        coverage_percentage=execution.coverage_percentage or 0.0,
        started_at=execution.started_at,
        completed_at=execution.completed_at,
        execution_notes=execution.execution_notes,
    )


# Test Results
@router.get("/results", response_model=List[TestResultResponse])
async def get_test_results(
    execution_id: Optional[UUID] = Query(None),
    test_case_id: Optional[UUID] = Query(None),
    status: Optional[TestStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get test results"""

    query = select(TestResult, TestCase.name.label("test_case_name")).join(
        TestCase, TestResult.test_case_id == TestCase.id
    )

    if execution_id:
        query = query.where(TestResult.execution_id == execution_id)

    if test_case_id:
        query = query.where(TestResult.test_case_id == test_case_id)

    if status:
        query = query.where(TestResult.status == status)

    query = query.offset(skip).limit(limit).order_by(TestResult.executed_at.desc())

    result = await db.execute(query)
    test_results = result.fetchall()

    return [
        TestResultResponse(
            id=tr.TestResult.id,
            test_case_id=tr.TestResult.test_case_id,
            test_case_name=tr.test_case_name,
            execution_id=tr.TestResult.execution_id,
            status=tr.TestResult.status,
            execution_time=tr.TestResult.execution_time,
            assertions_passed=tr.TestResult.assertions_passed or 0,
            assertions_failed=tr.TestResult.assertions_failed or 0,
            error_message=tr.TestResult.error_message,
            stack_trace=tr.TestResult.stack_trace,
            output_logs=tr.TestResult.output_logs or [],
            metadata=tr.TestResult.metadata or {},
            executed_at=tr.TestResult.executed_at,
        )
        for tr in test_results
    ]


# API Test Creation
@router.post(
    "/api-tests", response_model=TestCaseResponse, status_code=status.HTTP_201_CREATED
)
async def create_api_test(
    api_test: APITestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create API test case"""

    test_data = {
        "endpoint": api_test.endpoint,
        "method": api_test.method,
        "headers": api_test.headers,
        "request_data": api_test.request_data,
        "performance_threshold_ms": api_test.performance_threshold_ms,
    }

    expected_results = {
        "status_code": api_test.expected_status_code,
        "response_schema": api_test.expected_response_schema,
    }

    db_test_case = TestCase(
        id=uuid4(),
        name=api_test.name,
        description=f"API test for {api_test.method} {api_test.endpoint}",
        test_type=TestType.API,
        priority=TestPriority.MEDIUM,
        test_environment=TestEnvironment.TESTING,
        test_data=test_data,
        expected_results=expected_results,
        timeout_seconds=30,
        retry_count=0,
        tags=api_test.tags,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(db_test_case)
    await db.commit()
    await db.refresh(db_test_case)

    return TestCaseResponse(
        id=db_test_case.id,
        name=db_test_case.name,
        description=db_test_case.description,
        test_type=db_test_case.test_type,
        priority=db_test_case.priority,
        test_environment=db_test_case.test_environment,
        test_data=db_test_case.test_data,
        expected_results=db_test_case.expected_results,
        timeout_seconds=db_test_case.timeout_seconds,
        retry_count=db_test_case.retry_count,
        tags=db_test_case.tags,
        execution_count=0,
        last_execution=None,
        last_status=None,
        success_rate=0.0,
        average_execution_time=0.0,
        created_at=db_test_case.created_at,
        updated_at=db_test_case.updated_at,
    )


# Performance Test Creation
@router.post(
    "/performance-tests",
    response_model=TestCaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_performance_test(
    perf_test: PerformanceTestRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Create performance test case"""

    test_data = {
        "target_endpoint": perf_test.target_endpoint,
        "iterations": perf_test.iterations,
        "concurrent_users": perf_test.concurrent_users,
        "max_execution_time_ms": perf_test.max_execution_time_ms,
        "max_memory_usage_mb": perf_test.max_memory_usage_mb,
    }

    db_test_case = TestCase(
        id=uuid4(),
        name=perf_test.name,
        description=f"Performance test for {perf_test.target_endpoint}",
        test_type=TestType.PERFORMANCE,
        priority=TestPriority.HIGH,
        test_environment=TestEnvironment.TESTING,
        test_data=test_data,
        expected_results={},
        timeout_seconds=300,  # 5 minutes for performance tests
        retry_count=0,
        tags=perf_test.tags,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
        created_by=current_user.id,
    )

    db.add(db_test_case)
    await db.commit()
    await db.refresh(db_test_case)

    return TestCaseResponse(
        id=db_test_case.id,
        name=db_test_case.name,
        description=db_test_case.description,
        test_type=db_test_case.test_type,
        priority=db_test_case.priority,
        test_environment=db_test_case.test_environment,
        test_data=db_test_case.test_data,
        expected_results=db_test_case.expected_results,
        timeout_seconds=db_test_case.timeout_seconds,
        retry_count=db_test_case.retry_count,
        tags=db_test_case.tags,
        execution_count=0,
        last_execution=None,
        last_status=None,
        success_rate=0.0,
        average_execution_time=0.0,
        created_at=db_test_case.created_at,
        updated_at=db_test_case.updated_at,
    )


# Coverage and Quality Reports
@router.get("/coverage", response_model=CoverageReportResponse)
async def get_coverage_report(
    execution_id: Optional[UUID] = Query(None),
    current_user: User = Depends(get_current_active_user),
):
    """Get test coverage report"""

    # Generate coverage report using test automation engine
    coverage_report = (
        await test_automation_engine.test_runner.generate_coverage_report()
    )

    return CoverageReportResponse(
        coverage_percentage=coverage_report["coverage_percentage"],
        lines_covered=coverage_report["lines_covered"],
        lines_total=coverage_report["lines_total"],
        files_analyzed=coverage_report["files_analyzed"],
        branches_covered=coverage_report["branches_covered"],
        generated_at=datetime.fromisoformat(coverage_report["generated_at"]),
        details=coverage_report["details"],
    )


@router.get("/statistics")
async def get_test_statistics(
    period_days: int = Query(30, ge=1, le=365),
    test_environment: Optional[TestEnvironment] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """Get test execution statistics"""

    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=period_days)

    # Get execution statistics
    execution_stats = await db.execute(
        select(
            func.count(TestExecution.id).label("total_executions"),
            func.count(TestExecution.id)
            .filter(TestExecution.status == "completed")
            .label("completed_executions"),
            func.count(TestExecution.id)
            .filter(TestExecution.status == "failed")
            .label("failed_executions"),
            func.avg(TestExecution.execution_time).label("avg_execution_time"),
            func.avg(TestExecution.coverage_percentage).label("avg_coverage"),
        ).where(
            and_(
                TestExecution.started_at >= start_date,
                TestExecution.started_at <= end_date,
            )
        )
    )
    stats = execution_stats.first()

    # Get test result statistics
    result_stats = await db.execute(
        select(
            func.count(TestResult.id).label("total_test_results"),
            func.count(TestResult.id)
            .filter(TestResult.status == TestStatus.PASSED)
            .label("passed_results"),
            func.count(TestResult.id)
            .filter(TestResult.status == TestStatus.FAILED)
            .label("failed_results"),
            func.avg(TestResult.execution_time).label("avg_test_time"),
        ).where(
            and_(
                TestResult.executed_at >= start_date, TestResult.executed_at <= end_date
            )
        )
    )
    result_stats_data = result_stats.first()

    total_executions = stats.total_executions or 0
    completed_executions = stats.completed_executions or 0
    total_test_results = result_stats_data.total_test_results or 0
    passed_results = result_stats_data.passed_results or 0

    return {
        "period": {
            "days": period_days,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat(),
        },
        "executions": {
            "total": total_executions,
            "completed": completed_executions,
            "failed": stats.failed_executions or 0,
            "success_rate": (completed_executions / total_executions * 100)
            if total_executions > 0
            else 0,
            "average_execution_time": float(stats.avg_execution_time or 0),
            "average_coverage": float(stats.avg_coverage or 0),
        },
        "test_results": {
            "total": total_test_results,
            "passed": passed_results,
            "failed": result_stats_data.failed_results or 0,
            "success_rate": (passed_results / total_test_results * 100)
            if total_test_results > 0
            else 0,
            "average_test_time": float(result_stats_data.avg_test_time or 0),
        },
        "generated_at": datetime.utcnow().isoformat(),
    }


# CI/CD Integration
@router.post("/ci/pipeline")
async def run_ci_pipeline(
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_active_user),
):
    """Run CI/CD test pipeline"""

    # Execute CI pipeline in background
    background_tasks.add_task(_run_ci_pipeline)

    return {
        "status": "started",
        "message": "CI pipeline execution started",
        "started_at": datetime.utcnow().isoformat(),
    }


async def _run_ci_pipeline() -> None:
    """Execute CI pipeline"""
    try:
        # Initialize test suites if not already done
        from app.services.test_automation_engine import (
            initialize_test_suites,
            run_ci_pipeline,
        )

        await initialize_test_suites()

        # Run CI pipeline
        result = await run_ci_pipeline()

        logging.info(f"CI pipeline completed: {result['pipeline_passed']}")

    except Exception as e:
        logging.error(f"CI pipeline failed: {e}")


@router.get("/health")
async def get_testing_health(current_user: User = Depends(get_current_active_user)):
    """Get testing system health"""

    # Get test statistics from automation engine
    stats = await test_automation_engine.test_runner.get_test_statistics()

    # Determine health status
    health_status = "healthy"
    issues = []

    if stats.get("success_rate", 100) < 90:
        health_status = "degraded"
        issues.append("Low test success rate")

    if stats.get("average_coverage", 100) < 80:
        health_status = "degraded"
        issues.append("Low test coverage")

    return {
        "status": health_status,
        "issues": issues,
        "test_suites": len(test_automation_engine.test_pipelines),
        "pipelines": list(test_automation_engine.test_pipelines.keys()),
        "last_execution": None,  # Would get from recent executions
        "quality_gates": test_automation_engine.quality_gates,
        "checked_at": datetime.utcnow().isoformat(),
    }
