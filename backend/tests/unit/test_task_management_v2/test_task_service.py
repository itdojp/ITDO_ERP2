"""Unit tests for TaskService."""

import pytest
from sqlalchemy.orm import Session

from app.services.task import TaskService
from app.models.task import TaskStatus
from app.core.exceptions import PermissionDenied, InvalidTransition, CircularDependency, DependencyExists


class TestTaskService:
    """Test cases for TaskService."""

    def test_create_task_with_permission(self, db: Session):
        """Test UT-SVC-001: タスク作成（権限あり）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_create_task_without_permission(self, db: Session):
        """Test UT-SVC-002: タスク作成（権限なし）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_status_update_valid_transition(self, db: Session):
        """Test UT-SVC-003: ステータス更新（有効な遷移）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_status_update_invalid_transition(self, db: Session):
        """Test UT-SVC-004: ステータス更新（無効な遷移）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_assign_user_with_notification(self, db: Session):
        """Test UT-SVC-005: 担当者割り当て（通知付き）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_bulk_assign_users(self, db: Session):
        """Test UT-SVC-006: 複数担当者一括割り当て"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_add_dependency_no_circular(self, db: Session):
        """Test UT-SVC-007: 依存関係追加（循環なし）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_add_dependency_with_circular(self, db: Session):
        """Test UT-SVC-008: 依存関係追加（循環あり）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_delete_task_no_dependencies(self, db: Session):
        """Test UT-SVC-009: タスク削除（依存なし）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_delete_task_with_dependencies(self, db: Session):
        """Test UT-SVC-010: タスク削除（依存あり）"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_calculate_workload(self, db: Session):
        """Test UT-SVC-011: ワークロード計算"""
        raise NotImplementedError("TDD Red: Test not implemented")

    def test_calculate_critical_path(self, db: Session):
        """Test UT-SVC-012: クリティカルパス計算"""
        raise NotImplementedError("TDD Red: Test not implemented")