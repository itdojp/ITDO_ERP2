"""Performance tests for task management."""

import pytest
from locust import HttpUser, task, between
from datetime import datetime
import json


class TaskPerformanceUser(HttpUser):
    """Performance test user for task management."""
    
    wait_time = between(1, 3)
    
    def on_start(self):
        """Set up authentication before tests."""
        # Login and get auth token
        response = self.client.post("/api/v1/auth/login", json={
            "email": "test@example.com",
            "password": "password123"
        })
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def test_task_list_performance(self):
        """Test PT-001: タスク一覧取得 < 200ms (1000件)"""
        with self.client.get("/api/v1/tasks", headers=self.headers, catch_response=True) as response:
            if response.elapsed.total_seconds() > 0.2:
                response.failure(f"Response time too slow: {response.elapsed.total_seconds()}s")
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
    
    @task(2)
    def test_task_search_performance(self):
        """Test PT-002: タスク検索 < 500ms (10000件中検索)"""
        with self.client.get("/api/v1/tasks?search=test", headers=self.headers, catch_response=True) as response:
            if response.elapsed.total_seconds() > 0.5:
                response.failure(f"Response time too slow: {response.elapsed.total_seconds()}s")
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")
    
    @task(5)
    def test_task_create_performance(self):
        """Test PT-003: タスク作成 < 100ms (単一作成)"""
        data = {
            "title": f"Performance test task {datetime.now().isoformat()}",
            "project_id": 1,
            "priority": "MEDIUM"
        }
        with self.client.post("/api/v1/tasks", json=data, headers=self.headers, catch_response=True) as response:
            if response.elapsed.total_seconds() > 0.1:
                response.failure(f"Response time too slow: {response.elapsed.total_seconds()}s")
            elif response.status_code not in [200, 201]:
                response.failure(f"Got status code {response.status_code}")
    
    @task(1)
    def test_bulk_update_performance(self):
        """Test PT-004: 一括更新 < 1s (100件更新)"""
        task_ids = list(range(1, 101))  # 100 tasks
        data = {
            "task_ids": task_ids,
            "status": "IN_PROGRESS"
        }
        with self.client.patch("/api/v1/tasks/bulk", json=data, headers=self.headers, catch_response=True) as response:
            if response.elapsed.total_seconds() > 1.0:
                response.failure(f"Response time too slow: {response.elapsed.total_seconds()}s")
            elif response.status_code != 200:
                response.failure(f"Got status code {response.status_code}")


class ConcurrentEditUser(HttpUser):
    """Test PT-005: 同時編集 エラーなし (10ユーザー同時)"""
    
    wait_time = between(0.1, 0.5)
    
    def on_start(self):
        """Set up authentication before tests."""
        response = self.client.post("/api/v1/auth/login", json={
            "email": f"user{self.environment.runner.user_count}@example.com",
            "password": "password123"
        })
        self.token = response.json().get("access_token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        self.task_id = 1  # Shared task ID for concurrent editing
    
    @task
    def test_concurrent_edit(self):
        """Test concurrent task editing."""
        # Get current version
        response = self.client.get(f"/api/v1/tasks/{self.task_id}", headers=self.headers)
        if response.status_code == 200:
            task = response.json()
            version = task.get("version", 1)
            
            # Try to update
            data = {
                "title": f"Updated by user {self.environment.runner.user_count}",
                "version": version
            }
            update_response = self.client.patch(
                f"/api/v1/tasks/{self.task_id}", 
                json=data, 
                headers=self.headers
            )
            
            if update_response.status_code == 409:
                # Optimistic lock conflict - expected behavior
                pass
            elif update_response.status_code != 200:
                print(f"Unexpected status code: {update_response.status_code}")


class WebSocketLoadTest(HttpUser):
    """Test PT-006: WebSocket同時接続 1000接続 (メモリ使用量監視)"""
    
    wait_time = between(5, 10)
    
    def on_start(self):
        """Connect to WebSocket."""
        # Note: Locust doesn't natively support WebSocket
        # This is a placeholder for WebSocket load testing
        raise NotImplementedError("WebSocket load testing requires additional setup")
    
    @task
    def test_websocket_load(self):
        """Test WebSocket concurrent connections."""
        raise NotImplementedError("WebSocket load testing requires additional setup")