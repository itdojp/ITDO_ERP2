"""
Department model unit tests.

Following TDD approach - Red phase: Writing tests before implementation.
"""

import pytest
from sqlalchemy.exc import IntegrityError

from app.models.department import Department
from app.models.organization import Organization
from tests.factories import DepartmentFactory, OrganizationFactory


class TestDepartmentModel:
    """Test cases for Department model."""

    def test_create_department(self, db_session) -> None:
        """TEST-DEPT-001: 部門が正しく作成されることを確認."""
        # Given: 組織
        org = OrganizationFactory()
        db_session.commit()

        # When: 部門作成
        dept = Department(
            organization_id=org.id,
            code="SALES",
            name="営業部",
            name_kana="エイギョウブ",
            level=1,
            path="",
            sort_order=1,
        )
        db_session.add(dept)
        db_session.commit()

        # パスを更新
        dept.path = str(dept.id)
        db_session.commit()

        # Then:
        assert dept.id is not None
        assert dept.code == "SALES"
        assert dept.name == "営業部"
        assert dept.level == 1
        assert dept.parent_id is None
        assert dept.path == str(dept.id)
        assert dept.is_active is True

    def test_create_child_department(self, db_session) -> None:
        """TEST-DEPT-002: 子部門が正しく作成されることを確認."""
        # Given: 親部門
        org = OrganizationFactory()
        parent = DepartmentFactory(
            organization=org, code="SALES", name="営業部", level=1
        )
        db_session.commit()
        parent.path = str(parent.id)
        db_session.commit()

        # When: 子部門作成
        child = Department(
            organization_id=org.id,
            parent_id=parent.id,
            code="SALES_TOKYO",
            name="東京営業所",
            level=2,
            path=f"{parent.path}",
        )
        db_session.add(child)
        db_session.commit()

        # パスを更新
        child.path = f"{parent.path}/{child.id}"
        db_session.commit()

        # Then:
        assert child.parent_id == parent.id
        assert child.level == 2
        assert child.path == f"{parent.id}/{child.id}"
        assert child.parent.id == parent.id

    def test_department_level_limit(self, db_session) -> None:
        """TEST-DEPT-003: 3階層目の部門作成が拒否されることを確認."""
        # Given: 2階層の部門
        org = OrganizationFactory()
        parent = DepartmentFactory(organization=org, level=1)
        child = DepartmentFactory(organization=org, parent=parent, level=2)
        db_session.commit()

        # When/Then: 3階層目作成で例外
        with pytest.raises(ValueError, match="部門階層は2階層まで"):
            grandchild = Department(
                organization_id=org.id,
                parent_id=child.id,
                code="INVALID",
                name="無効な部門",
                level=3,
            )
            grandchild.validate_hierarchy()

    def test_unique_department_code_per_organization(self, db_session) -> None:
        """組織内で部門コードが一意であることを確認."""
        # Given: 既存部門
        org = OrganizationFactory()
        dept1 = DepartmentFactory(organization=org, code="HR")
        db_session.commit()

        # When/Then: 同じ組織内で同じコード
        dept2 = Department(organization_id=org.id, code="HR", name="人事部2", level=1)
        db_session.add(dept2)

        with pytest.raises(IntegrityError):
            db_session.commit()

    def test_department_code_unique_across_organizations(self, db_session) -> None:
        """異なる組織では同じ部門コードが使用可能なことを確認."""
        # Given: 組織1の部門
        org1 = OrganizationFactory(code="ORG1")
        dept1 = DepartmentFactory(organization=org1, code="HR")
        db_session.commit()

        # When: 組織2で同じコード
        org2 = OrganizationFactory(code="ORG2")
        dept2 = Department(
            organization_id=org2.id, code="HR", name="人事部", level=1, path=""
        )
        db_session.add(dept2)
        db_session.commit()

        # Then: 正常に作成される
        assert dept2.id is not None
        assert dept2.code == dept1.code
        assert dept2.organization_id != dept1.organization_id

    def test_department_cascade_delete(self, db_session) -> None:
        """親部門削除時に子部門も削除されることを確認."""
        # Given: 親子関係の部門
        org = OrganizationFactory()
        parent = DepartmentFactory(organization=org, level=1)
        child = DepartmentFactory(organization=org, parent=parent, level=2)
        db_session.commit()
        child_id = child.id

        # When: 親部門削除
        db_session.delete(parent)
        db_session.commit()

        # Then: 子部門も削除される
        assert db_session.query(Department).filter_by(id=child_id).first() is None

    def test_department_sort_order(self, db_session) -> None:
        """部門のソート順が正しく機能することを確認."""
        # Given: 複数部門
        org = OrganizationFactory()
        dept1 = DepartmentFactory(organization=org, sort_order=2)
        dept2 = DepartmentFactory(organization=org, sort_order=1)
        dept3 = DepartmentFactory(organization=org, sort_order=3)
        db_session.commit()

        # When: ソート順で取得
        depts = (
            db_session.query(Department)
            .filter_by(organization_id=org.id)
            .order_by(Department.sort_order)
            .all()
        )

        # Then:
        assert depts[0].id == dept2.id
        assert depts[1].id == dept1.id
        assert depts[2].id == dept3.id

    def test_department_tree_structure(self, db_session) -> None:
        """部門の階層構造が正しく取得できることを確認."""
        # Given: 階層構造
        org = OrganizationFactory()
        sales = DepartmentFactory(
            organization=org, code="SALES", name="営業部", level=1
        )
        tokyo = DepartmentFactory(
            organization=org, parent=sales, code="TOKYO", name="東京営業所", level=2
        )
        osaka = DepartmentFactory(
            organization=org, parent=sales, code="OSAKA", name="大阪営業所", level=2
        )
        db_session.commit()

        # When: 子部門取得
        children = sales.children

        # Then:
        assert len(children) == 2
        child_codes = [c.code for c in children]
        assert "TOKYO" in child_codes
        assert "OSAKA" in child_codes

    def test_department_path_update(self, db_session) -> None:
        """部門パスが正しく更新されることを確認."""
        # Given: 部門
        org = OrganizationFactory()
        dept = DepartmentFactory(organization=org, level=1)
        db_session.commit()

        # When: パス更新
        dept.update_path()
        db_session.commit()

        # Then:
        assert dept.path == str(dept.id)

    def test_department_full_path_name(self, db_session) -> None:
        """部門のフルパス名が正しく生成されることを確認."""
        # Given: 階層構造
        org = OrganizationFactory()
        parent = DepartmentFactory(organization=org, name="営業部", level=1)
        child = DepartmentFactory(
            organization=org, parent=parent, name="東京営業所", level=2
        )
        db_session.commit()

        # When: フルパス名取得
        full_path = child.get_full_path_name()

        # Then:
        assert full_path == "営業部 / 東京営業所"
