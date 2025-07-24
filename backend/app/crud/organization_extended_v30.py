import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.models.organization_extended import (
    Department,
    Organization,
    OrganizationAddress,
    OrganizationContact,
)
from app.schemas.organization_complete_v30 import (
    AddressCreate,
    ContactCreate,
    DepartmentCreate,
    DepartmentUpdate,
    OrganizationCreate,
    OrganizationUpdate,
)


class NotFoundError(Exception):
    pass


class DuplicateError(Exception):
    pass


class OrganizationCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, org_id: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.id == org_id).first()

    def get_by_code(self, code: str) -> Optional[Organization]:
        return self.db.query(Organization).filter(Organization.code == code).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        sort_by: str = "created_at",
        sort_desc: bool = True,
    ) -> tuple[List[Organization], int]:
        query = self.db.query(Organization)

        # フィルタリング
        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(Organization.is_active == filters["is_active"])
            if filters.get("organization_type"):
                query = query.filter(
                    Organization.organization_type == filters["organization_type"]
                )
            if filters.get("industry"):
                query = query.filter(Organization.industry == filters["industry"])
            if filters.get("country"):
                query = query.filter(Organization.country == filters["country"])
            if filters.get("parent_id"):
                query = query.filter(Organization.parent_id == filters["parent_id"])
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Organization.name.ilike(search),
                        Organization.code.ilike(search),
                        Organization.description.ilike(search),
                    )
                )

        # カウント
        total = query.count()

        # ソート
        order_by = getattr(Organization, sort_by, Organization.created_at)
        if sort_desc:
            order_by = order_by.desc()
        query = query.order_by(order_by)

        # ページネーション
        organizations = query.offset(skip).limit(limit).all()

        return organizations, total

    def create(self, org_in: OrganizationCreate) -> Organization:
        # 重複チェック
        if self.get_by_code(org_in.code):
            raise DuplicateError("Organization code already exists")

        # 親組織の確認
        parent = None
        level = 0
        path = f"/{org_in.code}"

        if org_in.parent_id:
            parent = self.get_by_id(org_in.parent_id)
            if not parent:
                raise NotFoundError("Parent organization not found")
            level = parent.level + 1
            path = f"{parent.path}/{org_in.code}"

        # 組織作成
        db_org = Organization(
            id=str(uuid.uuid4()),
            name=org_in.name,
            code=org_in.code,
            description=org_in.description,
            organization_type=org_in.organization_type,
            industry=org_in.industry,
            tax_id=org_in.tax_id,
            registration_number=org_in.registration_number,
            email=org_in.email,
            phone=org_in.phone,
            fax=org_in.fax,
            website=org_in.website,
            address_line1=org_in.address_line1,
            address_line2=org_in.address_line2,
            city=org_in.city,
            state=org_in.state,
            postal_code=org_in.postal_code,
            country=org_in.country,
            parent_id=org_in.parent_id,
            level=level,
            path=path,
            is_headquarters=org_in.is_headquarters,
            annual_revenue=org_in.annual_revenue,
            employee_count=org_in.employee_count,
            established_date=org_in.established_date,
            settings=org_in.settings,
        )

        self.db.add(db_org)
        self.db.commit()
        self.db.refresh(db_org)

        return db_org

    def update(self, org_id: str, org_in: OrganizationUpdate) -> Optional[Organization]:
        org = self.get_by_id(org_id)
        if not org:
            raise NotFoundError(f"Organization {org_id} not found")

        update_data = org_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(org, field, value)

        org.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(org)

        return org

    def delete(self, org_id: str) -> bool:
        org = self.get_by_id(org_id)
        if not org:
            raise NotFoundError(f"Organization {org_id} not found")

        # 子組織の確認
        children_count = (
            self.db.query(func.count(Organization.id))
            .filter(Organization.parent_id == org_id)
            .scalar()
        )

        if children_count > 0:
            raise ValueError("Cannot delete organization with child organizations")

        # ソフトデリート
        org.is_active = False
        org.updated_at = datetime.utcnow()

        self.db.commit()
        return True

    def get_hierarchy(self, org_id: str) -> Optional[Organization]:
        """組織の階層構造を取得"""
        return (
            self.db.query(Organization)
            .options(
                joinedload(Organization.children), joinedload(Organization.departments)
            )
            .filter(Organization.id == org_id)
            .first()
        )

    def get_tree(self, parent_id: str = None) -> List[Organization]:
        """組織ツリー構造を取得"""
        query = self.db.query(Organization).filter(Organization.is_active)

        if parent_id:
            query = query.filter(Organization.parent_id == parent_id)
        else:
            query = query.filter(Organization.parent_id.is_(None))

        return query.order_by(Organization.name).all()

    def get_statistics(self) -> Dict[str, Any]:
        """組織統計情報を取得"""
        total_orgs = self.db.query(func.count(Organization.id)).scalar()
        active_orgs = (
            self.db.query(func.count(Organization.id))
            .filter(Organization.is_active)
            .scalar()
        )
        headquarters_count = (
            self.db.query(func.count(Organization.id))
            .filter(Organization.is_headquarters)
            .scalar()
        )

        # タイプ別統計
        type_stats = {}
        type_results = (
            self.db.query(Organization.organization_type, func.count(Organization.id))
            .group_by(Organization.organization_type)
            .all()
        )
        for org_type, count in type_results:
            type_stats[org_type or "未設定"] = count

        # 業界別統計
        industry_stats = {}
        industry_results = (
            self.db.query(Organization.industry, func.count(Organization.id))
            .group_by(Organization.industry)
            .all()
        )
        for industry, count in industry_results:
            industry_stats[industry or "未設定"] = count

        # 国別統計
        country_stats = {}
        country_results = (
            self.db.query(Organization.country, func.count(Organization.id))
            .group_by(Organization.country)
            .all()
        )
        for country, count in country_results:
            country_stats[country or "未設定"] = count

        # 従業員数合計
        total_employees = (
            self.db.query(func.sum(Organization.employee_count))
            .filter(Organization.employee_count.isnot(None))
            .scalar()
            or 0
        )

        # 部署数合計
        total_departments = self.db.query(func.count(Department.id)).scalar()

        return {
            "total_organizations": total_orgs or 0,
            "active_organizations": active_orgs or 0,
            "inactive_organizations": (total_orgs or 0) - (active_orgs or 0),
            "headquarters_count": headquarters_count or 0,
            "by_type": type_stats,
            "by_industry": industry_stats,
            "by_country": country_stats,
            "total_employees": total_employees,
            "total_departments": total_departments or 0,
        }


class DepartmentCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_id(self, dept_id: str) -> Optional[Department]:
        return self.db.query(Department).filter(Department.id == dept_id).first()

    def get_multi(
        self,
        skip: int = 0,
        limit: int = 100,
        organization_id: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> tuple[List[Department], int]:
        query = self.db.query(Department)

        if organization_id:
            query = query.filter(Department.organization_id == organization_id)

        if filters:
            if filters.get("is_active") is not None:
                query = query.filter(Department.is_active == filters["is_active"])
            if filters.get("department_type"):
                query = query.filter(
                    Department.department_type == filters["department_type"]
                )
            if filters.get("search"):
                search = f"%{filters['search']}%"
                query = query.filter(
                    or_(Department.name.ilike(search), Department.code.ilike(search))
                )

        total = query.count()
        departments = query.offset(skip).limit(limit).all()

        return departments, total

    def create(self, dept_in: DepartmentCreate) -> Department:
        # 組織の存在確認
        org = (
            self.db.query(Organization)
            .filter(Organization.id == dept_in.organization_id)
            .first()
        )
        if not org:
            raise NotFoundError("Organization not found")

        # コードの重複チェック（組織内）
        existing = (
            self.db.query(Department)
            .filter(
                Department.organization_id == dept_in.organization_id,
                Department.code == dept_in.code,
            )
            .first()
        )
        if existing:
            raise DuplicateError("Department code already exists in this organization")

        db_dept = Department(
            id=str(uuid.uuid4()),
            name=dept_in.name,
            code=dept_in.code,
            description=dept_in.description,
            organization_id=dept_in.organization_id,
            parent_department_id=dept_in.parent_department_id,
            department_type=dept_in.department_type,
            cost_center=dept_in.cost_center,
            budget=dept_in.budget,
            location=dept_in.location,
            manager_id=dept_in.manager_id,
            settings=dept_in.settings,
        )

        self.db.add(db_dept)
        self.db.commit()
        self.db.refresh(db_dept)

        return db_dept

    def update(self, dept_id: str, dept_in: DepartmentUpdate) -> Optional[Department]:
        dept = self.get_by_id(dept_id)
        if not dept:
            raise NotFoundError(f"Department {dept_id} not found")

        update_data = dept_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(dept, field, value)

        dept.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(dept)

        return dept

    def delete(self, dept_id: str) -> bool:
        dept = self.get_by_id(dept_id)
        if not dept:
            raise NotFoundError(f"Department {dept_id} not found")

        # ソフトデリート
        dept.is_active = False
        dept.updated_at = datetime.utcnow()

        self.db.commit()
        return True


class AddressCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_organization(self, org_id: str) -> List[OrganizationAddress]:
        return (
            self.db.query(OrganizationAddress)
            .filter(OrganizationAddress.organization_id == org_id)
            .order_by(
                OrganizationAddress.is_primary.desc(), OrganizationAddress.created_at
            )
            .all()
        )

    def create(self, address_in: AddressCreate) -> OrganizationAddress:
        # プライマリアドレスの場合、他のプライマリを解除
        if address_in.is_primary:
            self.db.query(OrganizationAddress).filter(
                OrganizationAddress.organization_id == address_in.organization_id,
                OrganizationAddress.is_primary,
            ).update({"is_primary": False})

        db_address = OrganizationAddress(
            id=str(uuid.uuid4()),
            organization_id=address_in.organization_id,
            address_type=address_in.address_type,
            name=address_in.name,
            address_line1=address_in.address_line1,
            address_line2=address_in.address_line2,
            city=address_in.city,
            state=address_in.state,
            postal_code=address_in.postal_code,
            country=address_in.country,
            phone=address_in.phone,
            fax=address_in.fax,
            email=address_in.email,
            is_primary=address_in.is_primary,
            latitude=address_in.latitude,
            longitude=address_in.longitude,
        )

        self.db.add(db_address)
        self.db.commit()
        self.db.refresh(db_address)

        return db_address


class ContactCRUD:
    def __init__(self, db: Session):
        self.db = db

    def get_by_organization(self, org_id: str) -> List[OrganizationContact]:
        return (
            self.db.query(OrganizationContact)
            .filter(OrganizationContact.organization_id == org_id)
            .order_by(
                OrganizationContact.is_primary.desc(), OrganizationContact.created_at
            )
            .all()
        )

    def create(self, contact_in: ContactCreate) -> OrganizationContact:
        # プライマリ連絡先の場合、他のプライマリを解除
        if contact_in.is_primary:
            self.db.query(OrganizationContact).filter(
                OrganizationContact.organization_id == contact_in.organization_id,
                OrganizationContact.is_primary,
            ).update({"is_primary": False})

        db_contact = OrganizationContact(
            id=str(uuid.uuid4()),
            organization_id=contact_in.organization_id,
            name=contact_in.name,
            title=contact_in.title,
            department=contact_in.department,
            email=contact_in.email,
            phone=contact_in.phone,
            mobile=contact_in.mobile,
            contact_type=contact_in.contact_type,
            is_primary=contact_in.is_primary,
            notes=contact_in.notes,
        )

        self.db.add(db_contact)
        self.db.commit()
        self.db.refresh(db_contact)

        return db_contact
