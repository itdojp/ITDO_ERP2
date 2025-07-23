"""テストフィクスチャ自動生成システム"""
import json
import random
from datetime import datetime, timedelta
from typing import Any, Dict, List
import uuid

class TestDataGenerator:
    def __init__(self):
        self.fake_users = []
        self.fake_organizations = []
        self.fake_tasks = []

    def generate_user(self, index: int) -> Dict[str, Any]:
        """ユーザーデータ生成"""
        return {
            "id": str(uuid.uuid4()),
            "email": f"user{index}@example.com",
            "full_name": f"Test User {index}",
            "is_active": random.choice([True, True, True, False]),
            "created_at": (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
            "role": random.choice(["admin", "user", "manager"])
        }

    def generate_organization(self, index: int) -> Dict[str, Any]:
        """組織データ生成"""
        return {
            "id": str(uuid.uuid4()),
            "name": f"Organization {index}",
            "code": f"ORG{index:03d}",
            "is_active": True,
            "employee_count": random.randint(10, 1000),
            "created_at": (datetime.now() - timedelta(days=random.randint(30, 365))).isoformat()
        }

    def generate_task(self, index: int) -> Dict[str, Any]:
        """タスクデータ生成"""
        return {
            "id": str(uuid.uuid4()),
            "title": f"Task {index}: {random.choice(['Fix bug', 'Add feature', 'Update docs'])}",
            "description": f"Description for task {index}",
            "status": random.choice(["todo", "in_progress", "done"]),
            "priority": random.choice(["low", "medium", "high"]),
            "assignee_id": random.choice(self.fake_users)["id"] if self.fake_users else None,
            "due_date": (datetime.now() + timedelta(days=random.randint(1, 30))).isoformat()
        }

    def generate_all(self, count: int = 100):
        """全テストデータ生成"""
        # ユーザー生成
        for i in range(count):
            self.fake_users.append(self.generate_user(i))

        # 組織生成
        for i in range(count // 5):
            self.fake_organizations.append(self.generate_organization(i))

        # タスク生成
        for i in range(count * 2):
            self.fake_tasks.append(self.generate_task(i))

        return {
            "users": self.fake_users,
            "organizations": self.fake_organizations,
            "tasks": self.fake_tasks
        }

    def save_fixtures(self):
        """フィクスチャファイル保存"""
        data = self.generate_all()

        # Backend fixtures
        with open("backend/tests/fixtures/test_data.json", "w") as f:
            json.dump(data, f, indent=2)

        # Frontend fixtures
        with open("frontend/tests/fixtures/mockData.json", "w") as f:
            json.dump(data, f, indent=2)

        print(f"Generated {len(data['users'])} users, {len(data['organizations'])} orgs, {len(data['tasks'])} tasks")

if __name__ == "__main__":
    generator = TestDataGenerator()
    generator.save_fixtures()