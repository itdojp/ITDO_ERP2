import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from sqlalchemy import and_, asc, desc, or_, text
from sqlalchemy.orm import Session, joinedload

from app.models.category_extended import (
    Category,
    CategoryAttribute,
    CategoryAuditLog,
    CategoryPricingRule,
)
from app.schemas.category_v30 import (
    CategoryAttributeCreate,
    CategoryAttributeUpdate,
    CategoryCreate,
    CategoryPricingRuleCreate,
    CategoryPricingRuleUpdate,
    CategoryUpdate,
)


class NotFoundError(Exception):
    pass


class DuplicateError(Exception):
    pass


class InvalidOperationError(Exception):
    pass


class CategoryCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, category_id: str) -> Optional[Category]:
        return (
            self.db.query(Category)
            .options(
                joinedload(Category.parent),
                joinedload(Category.children),
                joinedload(Category.creator),
                joinedload(Category.updater),
            )
            .filter(Category.id == category_id)
            .first()
        )

    def get_by_code(self, category_code: str) -> Optional[Category]:
        return (
            self.db.query(Category)
            .filter(Category.category_code == category_code)
            .first()
        )

    def get_by_parent(self, parent_id: Optional[str] = None) -> List[Category]:
        """親カテゴリIDで子カテゴリを取得"""
        query = self.db.query(Category)
        if parent_id:
            query = query.filter(Category.parent_id == parent_id)
        else:
            query = query.filter(Category.parent_id.is_(None))

        return (
            query.filter(Category.is_active)
            .order_by(Category.sort_order, Category.category_name)
            .all()
        )

    def get_hierarchy_path(self, category_id: str) -> List[Category]:
        """カテゴリの階層パスを取得（ルートから現在まで）"""
        category = self.get_by_id(category_id)
        if not category:
            return []

        path = []
        current = category
        while current:
            path.insert(0, current)
            current = current.parent if current.parent_id else None

        return path

    def get_descendants(
        self, category_id: str, include_inactive: bool = False
    ) -> List[Category]:
        """すべての子孫カテゴリを取得"""
        # WITH RECURSIVE を使用して階層データを取得
        recursive_query = text(
            """
            WITH RECURSIVE category_tree AS (
                SELECT id, parent_id, category_name, level, is_active
                FROM categories
                WHERE id = :category_id

                UNION ALL

                SELECT c.id, c.parent_id, c.category_name, c.level, c.is_active
                FROM categories c
                INNER JOIN category_tree ct ON c.parent_id = ct.id
            )
            SELECT id FROM category_tree
            WHERE id != :category_id
            {}
            ORDER BY level, category_name
        """.format("" if include_inactive else "AND is_active = true")
        )

        result = self.db.execute(recursive_query, {"category_id": category_id})
        descendant_ids = [row[0] for row in result]

        if not descendant_ids:
            return []

        return (
            self.db.query(Category)
            .filter(Category.id.in_(descendant_ids))
            .order_by(Category.level, Category.sort_order, Category.category_name)
            .all()
        )

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Category], int]:
        query = self.db.query(Category)

        if filters:
            if filters.get("category_type"):
                query = query.filter(Category.category_type == filters["category_type"])
            if filters.get("parent_id") is not None:
                if filters["parent_id"] == "null":
                    query = query.filter(Category.parent_id.is_(None))
                else:
                    query = query.filter(Category.parent_id == filters["parent_id"])
            if filters.get("is_active") is not None:
                query = query.filter(Category.is_active == filters["is_active"])
            if filters.get("level"):
                query = query.filter(Category.level == filters["level"])
            if filters.get("industry_vertical"):
                query = query.filter(
                    Category.industry_vertical == filters["industry_vertical"]
                )
            if filters.get("business_unit"):
                query = query.filter(Category.business_unit == filters["business_unit"])
            if filters.get("tax_category"):
                query = query.filter(Category.tax_category == filters["tax_category"])
            if filters.get("lifecycle_stage"):
                query = query.filter(
                    Category.lifecycle_stage == filters["lifecycle_stage"]
                )
            if filters.get("profitability_rating"):
                query = query.filter(
                    Category.profitability_rating == filters["profitability_rating"]
                )
            if filters.get("abc_analysis_class"):
                query = query.filter(
                    Category.abc_analysis_class == filters["abc_analysis_class"]
                )
            if filters.get("search"):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Category.category_name.ilike(search_term),
                        Category.category_code.ilike(search_term),
                        Category.description.ilike(search_term),
                    )
                )
            if filters.get("tags"):
                # JSON array contains any of the specified tags
                tag_filters = []
                for tag in filters["tags"]:
                    tag_filters.append(Category.tags.contains([tag]))
                query = query.filter(or_(*tag_filters))

        total = query.count()

        # ソート
        sort_by = (
            filters.get("sort_by", "category_name") if filters else "category_name"
        )
        sort_order = filters.get("sort_order", "asc") if filters else "asc"

        sort_column = getattr(Category, sort_by, Category.category_name)
        if sort_order == "desc":
            query = query.order_by(desc(sort_column))
        else:
            query = query.order_by(asc(sort_column))

        categories = query.offset(skip).limit(limit).all()
        return categories, total

    def create(self, category_in: CategoryCreate, user_id: str) -> Category:
        # カテゴリコード重複チェック
        existing = self.get_by_code(category_in.category_code)
        if existing:
            raise DuplicateError(
                f"Category code '{category_in.category_code}' already exists"
            )

        # 親カテゴリ存在確認
        parent = None
        level = 1
        path = category_in.category_name
        path_ids = ""

        if category_in.parent_id:
            parent = self.get_by_id(category_in.parent_id)
            if not parent:
                raise NotFoundError(
                    f"Parent category {category_in.parent_id} not found"
                )
            if not parent.is_active:
                raise InvalidOperationError(
                    "Cannot create category under inactive parent"
                )

            level = parent.level + 1
            path = (
                f"{parent.path} > {category_in.category_name}"
                if parent.path
                else category_in.category_name
            )
            path_ids = (
                f"{parent.path_ids},{parent.id}" if parent.path_ids else parent.id
            )

        # URLスラッグ生成
        url_slug = category_in.url_slug
        if not url_slug:
            url_slug = self._generate_url_slug(category_in.category_name)

        db_category = Category(
            id=str(uuid.uuid4()),
            parent_id=category_in.parent_id,
            category_code=category_in.category_code,
            category_name=category_in.category_name,
            category_name_en=category_in.category_name_en,
            description=category_in.description,
            level=level,
            sort_order=category_in.sort_order,
            path=path,
            path_ids=path_ids,
            category_type=category_in.category_type,
            industry_vertical=category_in.industry_vertical,
            business_unit=category_in.business_unit,
            display_name=category_in.display_name,
            display_order=category_in.display_order,
            tax_category=category_in.tax_category,
            measurement_unit=category_in.measurement_unit,
            weight_unit=category_in.weight_unit,
            dimension_unit=category_in.dimension_unit,
            allow_sales=category_in.allow_sales,
            allow_purchase=category_in.allow_purchase,
            allow_inventory=category_in.allow_inventory,
            requires_serial_number=category_in.requires_serial_number,
            requires_lot_tracking=category_in.requires_lot_tracking,
            requires_expiry_tracking=category_in.requires_expiry_tracking,
            quality_control_required=category_in.quality_control_required,
            default_income_account=category_in.default_income_account,
            default_expense_account=category_in.default_expense_account,
            default_asset_account=category_in.default_asset_account,
            suggested_markup_percentage=category_in.suggested_markup_percentage,
            standard_cost_method=category_in.standard_cost_method,
            valuation_method=category_in.valuation_method,
            safety_stock_percentage=category_in.safety_stock_percentage,
            abc_analysis_class=category_in.abc_analysis_class,
            vendor_managed_inventory=category_in.vendor_managed_inventory,
            seasonality_pattern=category_in.seasonality_pattern,
            demand_pattern=category_in.demand_pattern,
            lifecycle_stage=category_in.lifecycle_stage,
            profitability_rating=category_in.profitability_rating,
            approval_required=category_in.approval_required,
            attributes=category_in.attributes,
            tags=category_in.tags,
            custom_fields=category_in.custom_fields,
            translations=category_in.translations,
            seo_title=category_in.seo_title,
            seo_description=category_in.seo_description,
            seo_keywords=category_in.seo_keywords,
            url_slug=url_slug,
            low_stock_alert_enabled=category_in.low_stock_alert_enabled,
            price_change_alert_enabled=category_in.price_change_alert_enabled,
            new_product_alert_enabled=category_in.new_product_alert_enabled,
            created_by=user_id,
        )

        self.db.add(db_category)
        self.db.commit()
        self.db.refresh(db_category)

        # 親カテゴリのis_leafを更新
        if parent:
            parent.is_leaf = False
            self.db.commit()

        # 監査ログ作成
        self._create_audit_log(db_category.id, "create", user_id, "Category created")

        return db_category

    def update(
        self, category_id: str, category_in: CategoryUpdate, user_id: str
    ) -> Optional[Category]:
        category = self.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")

        # 変更内容を記録
        changes = []
        update_data = category_in.dict(exclude_unset=True)

        for field, new_value in update_data.items():
            old_value = getattr(category, field, None)
            if old_value != new_value:
                changes.append(
                    {
                        "field": field,
                        "old_value": str(old_value) if old_value is not None else None,
                        "new_value": str(new_value) if new_value is not None else None,
                    }
                )
                setattr(category, field, new_value)

        if changes:
            category.updated_at = datetime.utcnow()
            category.updated_by = user_id

            # パスの再計算が必要な場合
            if "category_name" in update_data:
                self._update_category_paths(category)

            self.db.commit()
            self.db.refresh(category)

            # 監査ログ作成
            for change in changes:
                self._create_audit_log(
                    category_id,
                    "update",
                    user_id,
                    f"Updated {change['field']}: {change['old_value']} -> {change['new_value']}",
                )

        return category

    def activate(self, category_id: str, user_id: str) -> Category:
        """カテゴリをアクティブ化"""
        category = self.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")

        if category.is_active:
            return category

        category.is_active = True
        category.updated_at = datetime.utcnow()
        category.updated_by = user_id

        self.db.commit()
        self.db.refresh(category)

        self._create_audit_log(category_id, "activate", user_id, "Category activated")
        return category

    def deactivate(self, category_id: str, user_id: str) -> Category:
        """カテゴリを非アクティブ化"""
        category = self.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")

        # 子カテゴリがある場合は非アクティブ化できない
        children = self.get_by_parent(category_id)
        if children:
            raise InvalidOperationError(
                "Cannot deactivate category with active children"
            )

        # アクティブな商品がある場合の確認（実装時に追加）
        # if category.product_count > 0:
        #     raise InvalidOperationError("Cannot deactivate category with active products")

        if not category.is_active:
            return category

        category.is_active = False
        category.updated_at = datetime.utcnow()
        category.updated_by = user_id

        self.db.commit()
        self.db.refresh(category)

        self._create_audit_log(
            category_id, "deactivate", user_id, "Category deactivated"
        )
        return category

    def move_category(
        self, category_id: str, new_parent_id: Optional[str], user_id: str
    ) -> Category:
        """カテゴリを別の親の下に移動"""
        category = self.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")

        # 循環参照チェック
        if new_parent_id:
            if new_parent_id == category_id:
                raise InvalidOperationError("Cannot move category to itself")

            new_parent = self.get_by_id(new_parent_id)
            if not new_parent:
                raise NotFoundError(f"New parent category {new_parent_id} not found")

            # 新しい親が現在のカテゴリの子孫でないことを確認
            descendants = self.get_descendants(category_id)
            if any(d.id == new_parent_id for d in descendants):
                raise InvalidOperationError(
                    "Cannot move category under its own descendant"
                )

        old_parent_id = category.parent_id
        category.parent_id = new_parent_id

        # レベルとパスの更新
        self._update_category_hierarchy(category)

        category.updated_at = datetime.utcnow()
        category.updated_by = user_id

        self.db.commit()
        self.db.refresh(category)

        # 旧親と新親のis_leafを更新
        self._update_parent_leaf_status(old_parent_id)
        self._update_parent_leaf_status(new_parent_id)

        self._create_audit_log(
            category_id,
            "move",
            user_id,
            f"Moved from parent {old_parent_id} to {new_parent_id}",
        )

        return category

    def delete(self, category_id: str, user_id: str) -> bool:
        """カテゴリを削除"""
        category = self.get_by_id(category_id)
        if not category:
            raise NotFoundError(f"Category {category_id} not found")

        # 子カテゴリがある場合は削除できない
        children = self.get_by_parent(category_id)
        if children:
            raise InvalidOperationError("Cannot delete category with children")

        # 商品がある場合は削除できない（実装時に追加）
        # if category.product_count > 0:
        #     raise InvalidOperationError("Cannot delete category with products")

        parent_id = category.parent_id

        self.db.delete(category)
        self.db.commit()

        # 親のis_leafを更新
        self._update_parent_leaf_status(parent_id)

        self._create_audit_log(category_id, "delete", user_id, "Category deleted")

        return True

    def get_analytics(self, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """カテゴリ分析データを取得"""
        base_query = self.db.query(Category)

        if filters:
            if filters.get("date_from"):
                base_query = base_query.filter(
                    Category.created_at >= filters["date_from"]
                )
            if filters.get("date_to"):
                base_query = base_query.filter(
                    Category.created_at <= filters["date_to"]
                )

        categories = base_query.all()

        total_categories = len(categories)
        active_categories = len([c for c in categories if c.is_active])
        inactive_categories = total_categories - active_categories
        leaf_categories = len([c for c in categories if c.is_leaf])

        # 階層深度統計
        levels = [c.level for c in categories]
        avg_hierarchy_depth = sum(levels) / len(levels) if levels else 0
        max_hierarchy_depth = max(levels) if levels else 0

        # タイプ別分布
        categories_by_type = {}
        for category in categories:
            cat_type = category.category_type
            categories_by_type[cat_type] = categories_by_type.get(cat_type, 0) + 1

        # レベル別分布
        categories_by_level = {}
        for level in levels:
            categories_by_level[level] = categories_by_level.get(level, 0) + 1

        # トップカテゴリ（商品数別）
        top_categories_by_product_count = [
            {
                "id": c.id,
                "name": c.category_name,
                "product_count": c.product_count,
                "level": c.level,
            }
            for c in sorted(categories, key=lambda x: x.product_count, reverse=True)[
                :10
            ]
            if c.product_count > 0
        ]

        # トップカテゴリ（売上別）
        top_categories_by_sales = [
            {
                "id": c.id,
                "name": c.category_name,
                "total_sales": float(c.total_sales_amount),
                "margin_percentage": float(c.avg_margin_percentage)
                if c.avg_margin_percentage
                else 0,
            }
            for c in sorted(
                categories, key=lambda x: x.total_sales_amount, reverse=True
            )[:10]
            if c.total_sales_amount > 0
        ]

        # 要注意カテゴリ
        categories_needing_attention = []
        for c in categories:
            issues = []
            if not c.is_active:
                issues.append("inactive")
            if c.product_count == 0 and c.is_leaf:
                issues.append("no_products")
            if (
                c.last_activity_date
                and (datetime.utcnow() - c.last_activity_date).days > 90
            ):
                issues.append("no_recent_activity")

            if issues:
                categories_needing_attention.append(
                    {
                        "id": c.id,
                        "name": c.category_name,
                        "issues": issues,
                        "product_count": c.product_count,
                    }
                )

        # 分類体系完成度
        taxonomy_completeness = {
            "categories_with_description": len(
                [c for c in categories if c.description]
            ),
            "categories_with_attributes": len([c for c in categories if c.attributes]),
            "categories_with_seo": len([c for c in categories if c.seo_title]),
            "categories_with_translations": len(
                [c for c in categories if c.translations]
            ),
        }

        return {
            "total_categories": total_categories,
            "active_categories": active_categories,
            "inactive_categories": inactive_categories,
            "leaf_categories": leaf_categories,
            "avg_hierarchy_depth": avg_hierarchy_depth,
            "max_hierarchy_depth": max_hierarchy_depth,
            "categories_by_type": categories_by_type,
            "categories_by_level": categories_by_level,
            "top_categories_by_product_count": top_categories_by_product_count,
            "top_categories_by_sales": top_categories_by_sales,
            "categories_needing_attention": categories_needing_attention,
            "taxonomy_completeness": taxonomy_completeness,
        }

    def get_tree_structure(
        self, root_id: Optional[str] = None, include_inactive: bool = False
    ) -> List[Dict[str, Any]]:
        """階層ツリー構造でカテゴリを取得"""
        if root_id:
            root_categories = [self.get_by_id(root_id)]
            if not root_categories[0]:
                return []
        else:
            root_categories = self.get_by_parent(None)

        def build_tree(categories) -> dict:
            tree = []
            for category in categories:
                if not include_inactive and not category.is_active:
                    continue

                children = self.get_by_parent(category.id)
                node = {
                    "id": category.id,
                    "category_code": category.category_code,
                    "category_name": category.category_name,
                    "level": category.level,
                    "is_active": category.is_active,
                    "is_leaf": category.is_leaf,
                    "product_count": category.product_count,
                    "children": build_tree(children) if children else [],
                }
                tree.append(node)
            return tree

        return build_tree(root_categories)

    def _generate_url_slug(self, name: str) -> str:
        """URLスラッグを生成"""
        import re

        # 日本語文字を除去してスラッグ生成
        slug = re.sub(r"[^\w\s-]", "", name.lower())
        slug = re.sub(r"[\s_-]+", "-", slug)
        slug = slug.strip("-")

        # 重複チェック
        base_slug = slug
        counter = 1
        while self.db.query(Category).filter(Category.url_slug == slug).first():
            slug = f"{base_slug}-{counter}"
            counter += 1

        return slug

    def _update_category_paths(self, category: Category) -> dict:
        """カテゴリパスを更新"""
        path_parts = []
        path_ids_parts = []
        current = category

        while current.parent:
            current = current.parent
            path_parts.insert(0, current.category_name)
            path_ids_parts.insert(0, current.id)

        path_parts.append(category.category_name)

        category.path = " > ".join(path_parts)
        category.path_ids = ",".join(path_ids_parts) if path_ids_parts else ""

        # 子孫カテゴリのパスも更新
        descendants = self.get_descendants(category.id)
        for descendant in descendants:
            self._update_category_paths(descendant)

    def _update_category_hierarchy(self, category: Category) -> dict:
        """カテゴリ階層情報を更新"""
        if category.parent_id:
            parent = self.get_by_id(category.parent_id)
            category.level = parent.level + 1
        else:
            category.level = 1

        self._update_category_paths(category)

        # 子孫カテゴリの階層も更新
        descendants = self.get_descendants(category.id)
        for descendant in descendants:
            self._update_category_hierarchy(descendant)

    def _update_parent_leaf_status(self, parent_id: Optional[str]) -> dict:
        """親カテゴリのis_leafステータスを更新"""
        if not parent_id:
            return

        parent = self.get_by_id(parent_id)
        if parent:
            children = self.get_by_parent(parent_id)
            parent.is_leaf = len(children) == 0
            self.db.commit()

    def _create_audit_log(
        self, category_id: str, action: str, user_id: str, description: str
    ):
        """監査ログを作成"""
        audit_log = CategoryAuditLog(
            id=str(uuid.uuid4()),
            category_id=category_id,
            action=action,
            user_id=user_id,
            change_reason=description,
            integration_source="api",
        )
        self.db.add(audit_log)
        self.db.commit()


class CategoryAttributeCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, attribute_id: str) -> Optional[CategoryAttribute]:
        return (
            self.db.query(CategoryAttribute)
            .filter(CategoryAttribute.id == attribute_id)
            .first()
        )

    def get_by_category(self, category_id: str) -> List[CategoryAttribute]:
        return (
            self.db.query(CategoryAttribute)
            .filter(CategoryAttribute.category_id == category_id)
            .order_by(CategoryAttribute.display_order, CategoryAttribute.attribute_name)
            .all()
        )

    def get_by_code(
        self, category_id: str, attribute_code: str
    ) -> Optional[CategoryAttribute]:
        return (
            self.db.query(CategoryAttribute)
            .filter(
                and_(
                    CategoryAttribute.category_id == category_id,
                    CategoryAttribute.attribute_code == attribute_code,
                )
            )
            .first()
        )

    def create(
        self, attribute_in: CategoryAttributeCreate, user_id: str
    ) -> CategoryAttribute:
        # 属性コード重複チェック
        existing = self.get_by_code(
            attribute_in.category_id, attribute_in.attribute_code
        )
        if existing:
            raise DuplicateError(
                f"Attribute code '{attribute_in.attribute_code}' already exists in this category"
            )

        db_attribute = CategoryAttribute(
            id=str(uuid.uuid4()),
            category_id=attribute_in.category_id,
            attribute_name=attribute_in.attribute_name,
            attribute_name_en=attribute_in.attribute_name_en,
            attribute_code=attribute_in.attribute_code,
            display_name=attribute_in.display_name,
            data_type=attribute_in.data_type,
            is_required=attribute_in.is_required,
            is_unique=attribute_in.is_unique,
            is_searchable=attribute_in.is_searchable,
            is_filterable=attribute_in.is_filterable,
            is_visible_in_list=attribute_in.is_visible_in_list,
            display_order=attribute_in.display_order,
            group_name=attribute_in.group_name,
            help_text=attribute_in.help_text,
            placeholder_text=attribute_in.placeholder_text,
            min_value=attribute_in.min_value,
            max_value=attribute_in.max_value,
            min_length=attribute_in.min_length,
            max_length=attribute_in.max_length,
            regex_pattern=attribute_in.regex_pattern,
            default_value=attribute_in.default_value,
            option_values=attribute_in.option_values,
            unit=attribute_in.unit,
            unit_type=attribute_in.unit_type,
            validation_rules=attribute_in.validation_rules,
            business_rules=attribute_in.business_rules,
            translations=attribute_in.translations,
            inherit_from_parent=attribute_in.inherit_from_parent,
            shared_across_categories=attribute_in.shared_across_categories,
            created_by=user_id,
        )

        self.db.add(db_attribute)
        self.db.commit()
        self.db.refresh(db_attribute)

        return db_attribute

    def update(
        self, attribute_id: str, attribute_in: CategoryAttributeUpdate
    ) -> Optional[CategoryAttribute]:
        attribute = self.get_by_id(attribute_id)
        if not attribute:
            raise NotFoundError(f"Attribute {attribute_id} not found")

        update_data = attribute_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(attribute, field, value)

        attribute.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(attribute)

        return attribute

    def delete(self, attribute_id: str) -> bool:
        attribute = self.get_by_id(attribute_id)
        if not attribute:
            raise NotFoundError(f"Attribute {attribute_id} not found")

        self.db.delete(attribute)
        self.db.commit()

        return True


class CategoryPricingRuleCRUD:
    def __init__(self, db: Session) -> dict:
        self.db = db

    def get_by_id(self, rule_id: str) -> Optional[CategoryPricingRule]:
        return (
            self.db.query(CategoryPricingRule)
            .filter(CategoryPricingRule.id == rule_id)
            .first()
        )

    def get_by_category(
        self, category_id: str, active_only: bool = True
    ) -> List[CategoryPricingRule]:
        query = self.db.query(CategoryPricingRule).filter(
            CategoryPricingRule.category_id == category_id
        )

        if active_only:
            query = query.filter(CategoryPricingRule.is_active)

        return query.order_by(CategoryPricingRule.priority.desc()).all()

    def get_multi(
        self, skip: int = 0, limit: int = 100, filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[CategoryPricingRule], int]:
        query = self.db.query(CategoryPricingRule)

        if filters:
            if filters.get("category_id"):
                query = query.filter(
                    CategoryPricingRule.category_id == filters["category_id"]
                )
            if filters.get("rule_type"):
                query = query.filter(
                    CategoryPricingRule.rule_type == filters["rule_type"]
                )
            if filters.get("is_active") is not None:
                query = query.filter(
                    CategoryPricingRule.is_active == filters["is_active"]
                )
            if filters.get("currency"):
                query = query.filter(
                    CategoryPricingRule.currency == filters["currency"]
                )

        total = query.count()
        rules = (
            query.offset(skip)
            .limit(limit)
            .order_by(
                CategoryPricingRule.priority.desc(),
                CategoryPricingRule.created_at.desc(),
            )
            .all()
        )

        return rules, total

    def create(
        self, rule_in: CategoryPricingRuleCreate, user_id: str
    ) -> CategoryPricingRule:
        db_rule = CategoryPricingRule(
            id=str(uuid.uuid4()),
            category_id=rule_in.category_id,
            rule_name=rule_in.rule_name,
            rule_code=rule_in.rule_code,
            description=rule_in.description,
            rule_type=rule_in.rule_type,
            priority=rule_in.priority,
            is_active=rule_in.is_active,
            effective_date=rule_in.effective_date,
            expiry_date=rule_in.expiry_date,
            customer_segments=rule_in.customer_segments,
            minimum_quantity=rule_in.minimum_quantity,
            maximum_quantity=rule_in.maximum_quantity,
            minimum_amount=rule_in.minimum_amount,
            markup_percentage=rule_in.markup_percentage,
            discount_percentage=rule_in.discount_percentage,
            fixed_amount=rule_in.fixed_amount,
            cost_multiplier=rule_in.cost_multiplier,
            price_tiers=rule_in.price_tiers,
            volume_discounts=rule_in.volume_discounts,
            currency=rule_in.currency,
            region_codes=rule_in.region_codes,
            exchange_rate_factor=rule_in.exchange_rate_factor,
            competitor_price_factor=rule_in.competitor_price_factor,
            market_position=rule_in.market_position,
            price_elasticity=rule_in.price_elasticity,
            approval_required=rule_in.approval_required,
            created_by=user_id,
        )

        self.db.add(db_rule)
        self.db.commit()
        self.db.refresh(db_rule)

        return db_rule

    def update(
        self, rule_id: str, rule_in: CategoryPricingRuleUpdate
    ) -> Optional[CategoryPricingRule]:
        rule = self.get_by_id(rule_id)
        if not rule:
            raise NotFoundError(f"Pricing rule {rule_id} not found")

        update_data = rule_in.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(rule, field, value)

        rule.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def activate(self, rule_id: str) -> CategoryPricingRule:
        rule = self.get_by_id(rule_id)
        if not rule:
            raise NotFoundError(f"Pricing rule {rule_id} not found")

        rule.is_active = True
        rule.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def deactivate(self, rule_id: str) -> CategoryPricingRule:
        rule = self.get_by_id(rule_id)
        if not rule:
            raise NotFoundError(f"Pricing rule {rule_id} not found")

        rule.is_active = False
        rule.updated_at = datetime.utcnow()

        self.db.commit()
        self.db.refresh(rule)

        return rule

    def delete(self, rule_id: str) -> bool:
        rule = self.get_by_id(rule_id)
        if not rule:
            raise NotFoundError(f"Pricing rule {rule_id} not found")

        self.db.delete(rule)
        self.db.commit()

        return True
