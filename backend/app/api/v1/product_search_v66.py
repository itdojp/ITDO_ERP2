"""
ITDO ERP Backend - Advanced Product Search & Filter System v66
Elasticsearch-powered search with advanced filtering, faceted search, and recommendations
Day 8: Advanced Product Search & Filter Implementation
"""

from __future__ import annotations

import json
import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Union

import aioredis
from elasticsearch import AsyncElasticsearch
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy import (
    DECIMAL,
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    String,
    Text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.sql import and_, func, text

from app.core.database import get_db
from app.core.security import get_current_user
from app.models.base import BaseTable

# ============================================================================
# Configuration and Constants
# ============================================================================


class SearchScope(str, Enum):
    """Search scope enumeration"""

    ALL = "all"
    NAME = "name"
    DESCRIPTION = "description"
    SKU = "sku"
    CATEGORY = "category"
    BRAND = "brand"
    TAGS = "tags"
    ATTRIBUTES = "attributes"


class SortOption(str, Enum):
    """Sort option enumeration"""

    RELEVANCE = "relevance"
    PRICE_ASC = "price_asc"
    PRICE_DESC = "price_desc"
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    NEWEST = "newest"
    OLDEST = "oldest"
    POPULARITY = "popularity"
    RATING = "rating"
    AVAILABILITY = "availability"


class FacetType(str, Enum):
    """Facet type enumeration"""

    TERMS = "terms"
    RANGE = "range"
    HISTOGRAM = "histogram"
    DATE_HISTOGRAM = "date_histogram"
    NESTED = "nested"


# Elasticsearch configuration
ES_CONFIG = {
    "hosts": ["http://localhost:9200"],
    "index_name": "products",
    "settings": {
        "number_of_shards": 3,
        "number_of_replicas": 1,
        "analysis": {
            "analyzer": {
                "product_analyzer": {
                    "type": "custom",
                    "tokenizer": "standard",
                    "filter": ["lowercase", "stop", "snowball", "synonym"],
                },
                "autocomplete_analyzer": {
                    "type": "custom",
                    "tokenizer": "autocomplete_tokenizer",
                    "filter": ["lowercase"],
                },
            },
            "tokenizer": {
                "autocomplete_tokenizer": {
                    "type": "edge_ngram",
                    "min_gram": 1,
                    "max_gram": 20,
                    "token_chars": ["letter", "digit"],
                }
            },
            "filter": {
                "synonym": {
                    "type": "synonym",
                    "synonyms": [
                        "laptop,notebook,computer",
                        "phone,mobile,smartphone",
                        "tv,television",
                    ],
                }
            },
        },
    },
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "sku": {"type": "keyword"},
            "name": {
                "type": "text",
                "analyzer": "product_analyzer",
                "fields": {
                    "keyword": {"type": "keyword"},
                    "autocomplete": {
                        "type": "text",
                        "analyzer": "autocomplete_analyzer",
                    },
                },
            },
            "description": {"type": "text", "analyzer": "product_analyzer"},
            "short_description": {"type": "text", "analyzer": "product_analyzer"},
            "category": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "slug": {"type": "keyword"},
                    "hierarchy": {"type": "keyword"},
                },
            },
            "brand": {
                "type": "nested",
                "properties": {
                    "id": {"type": "keyword"},
                    "name": {"type": "keyword"},
                    "slug": {"type": "keyword"},
                },
            },
            "price": {"type": "scaled_float", "scaling_factor": 100},
            "compare_at_price": {"type": "scaled_float", "scaling_factor": 100},
            "cost_price": {"type": "scaled_float", "scaling_factor": 100},
            "status": {"type": "keyword"},
            "product_type": {"type": "keyword"},
            "is_visible": {"type": "boolean"},
            "is_featured": {"type": "boolean"},
            "inventory_quantity": {"type": "integer"},
            "track_inventory": {"type": "boolean"},
            "weight": {"type": "float"},
            "dimensions": {
                "type": "object",
                "properties": {
                    "length": {"type": "float"},
                    "width": {"type": "float"},
                    "height": {"type": "float"},
                    "unit": {"type": "keyword"},
                },
            },
            "tags": {"type": "keyword"},
            "attributes": {
                "type": "nested",
                "properties": {
                    "name": {"type": "keyword"},
                    "value": {"type": "keyword"},
                    "display_value": {"type": "text"},
                },
            },
            "images": {
                "type": "nested",
                "properties": {
                    "url": {"type": "keyword"},
                    "alt": {"type": "text"},
                    "is_primary": {"type": "boolean"},
                },
            },
            "rating": {
                "type": "object",
                "properties": {
                    "average": {"type": "float"},
                    "count": {"type": "integer"},
                },
            },
            "sales_count": {"type": "integer"},
            "view_count": {"type": "integer"},
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"},
            "published_at": {"type": "date"},
            "search_keywords": {"type": "text", "analyzer": "product_analyzer"},
            "suggest": {"type": "completion", "analyzer": "product_analyzer"},
        }
    },
}

# ============================================================================
# Database Models
# ============================================================================


class SearchIndex(BaseTable):
    """Search index management model"""

    __tablename__ = "search_indexes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False, unique=True)
    index_type = Column(String(50), nullable=False)  # elasticsearch, solr, etc.
    configuration = Column(JSON, nullable=False)
    is_active = Column(Boolean, default=True)
    last_full_sync = Column(DateTime)
    last_incremental_sync = Column(DateTime)

    # Statistics
    total_documents = Column(Integer, default=0)
    index_size_mb = Column(Integer, default=0)
    avg_query_time_ms = Column(Integer, default=0)

    __table_args__ = (
        Index("idx_search_index_active", "is_active"),
        Index("idx_search_index_type", "index_type"),
    )


class SearchQuery(BaseTable):
    """Search query logging model"""

    __tablename__ = "search_queries"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    query_text = Column(Text, nullable=False)
    filters = Column(JSON)
    sort_by = Column(String(100))
    results_count = Column(Integer)
    execution_time_ms = Column(Integer)

    # User context
    user_id = Column(UUID(as_uuid=True))
    session_id = Column(String(100))
    ip_address = Column(String(45))
    user_agent = Column(Text)

    # Results interaction
    clicked_results = Column(JSON)  # Products that were clicked
    conversion_product_id = Column(UUID(as_uuid=True))  # Product that was purchased

    __table_args__ = (
        Index("idx_search_query_text", "query_text"),
        Index("idx_search_query_user", "user_id"),
        Index("idx_search_query_date", "created_at"),
    )


class SearchFacet(BaseTable):
    """Search facet configuration model"""

    __tablename__ = "search_facets"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(200), nullable=False)
    field_name = Column(String(200), nullable=False)
    facet_type = Column(String(50), nullable=False)
    display_name = Column(String(200), nullable=False)

    # Configuration
    configuration = Column(JSON)  # Facet-specific settings
    is_active = Column(Boolean, default=True)
    sort_order = Column(Integer, default=0)

    # Display settings
    show_count = Column(Boolean, default=True)
    max_values = Column(Integer, default=10)
    min_doc_count = Column(Integer, default=1)

    __table_args__ = (
        Index("idx_facet_field", "field_name"),
        Index("idx_facet_active", "is_active"),
        Index("idx_facet_order", "sort_order"),
    )


class ProductPopularity(BaseTable):
    """Product popularity tracking model"""

    __tablename__ = "product_popularity"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_id = Column(UUID(as_uuid=True), nullable=False, unique=True)

    # Popularity metrics
    view_count = Column(Integer, default=0)
    search_count = Column(Integer, default=0)
    cart_add_count = Column(Integer, default=0)
    purchase_count = Column(Integer, default=0)
    wishlist_count = Column(Integer, default=0)

    # Calculated scores
    popularity_score = Column(DECIMAL(10, 4), default=0)
    trending_score = Column(DECIMAL(10, 4), default=0)

    # Time-based metrics
    last_viewed = Column(DateTime)
    last_purchased = Column(DateTime)

    __table_args__ = (
        Index("idx_popularity_product", "product_id"),
        Index("idx_popularity_score", "popularity_score"),
        Index("idx_trending_score", "trending_score"),
    )


# ============================================================================
# Pydantic Schemas
# ============================================================================


class SearchRequest(BaseModel):
    query: Optional[str] = None
    scope: SearchScope = SearchScope.ALL
    filters: Optional[Dict[str, Any]] = None
    facets: Optional[List[str]] = None
    sort: SortOption = SortOption.RELEVANCE
    page: int = Field(1, ge=1)
    size: int = Field(20, ge=1, le=100)
    include_suggestions: bool = True
    include_facets: bool = True
    include_aggregations: bool = False
    highlight: bool = True


class SearchFilter(BaseModel):
    field: str
    operator: str = "eq"  # eq, ne, gt, gte, lt, lte, in, not_in, range, exists
    value: Union[str, int, float, List[str], Dict[str, Any]]
    boost: Optional[float] = None


class FacetRequest(BaseModel):
    name: str
    field: str
    facet_type: FacetType = FacetType.TERMS
    size: int = 10
    configuration: Optional[Dict[str, Any]] = None


class SearchResponse(BaseModel):
    query: Optional[str]
    total: int
    page: int
    size: int
    pages: int
    execution_time_ms: int
    products: List[Dict[str, Any]]
    facets: Optional[Dict[str, Any]] = None
    suggestions: Optional[List[str]] = None
    aggregations: Optional[Dict[str, Any]] = None
    did_you_mean: Optional[str] = None


class AutocompleteRequest(BaseModel):
    query: str = Field(..., min_length=1)
    size: int = Field(10, ge=1, le=50)
    categories: Optional[List[str]] = None
    include_products: bool = True
    include_categories: bool = True
    include_brands: bool = True


class AutocompleteResponse(BaseModel):
    query: str
    suggestions: List[Dict[str, Any]]
    execution_time_ms: int


class RecommendationRequest(BaseModel):
    product_id: Optional[uuid.UUID] = None
    user_id: Optional[uuid.UUID] = None
    category_id: Optional[uuid.UUID] = None
    recommendation_type: str = "related"  # related, similar, popular, trending
    size: int = Field(10, ge=1, le=50)
    exclude_ids: Optional[List[uuid.UUID]] = None


class SearchAnalytics(BaseModel):
    total_queries: int
    avg_execution_time: float
    popular_queries: List[Dict[str, Any]]
    no_results_queries: List[str]
    top_clicked_results: List[Dict[str, Any]]
    conversion_rate: float


# ============================================================================
# Service Classes
# ============================================================================


class ElasticsearchService:
    """Elasticsearch service for product search"""

    def __init__(self, db: AsyncSession, redis_client: aioredis.Redis) -> dict:
        self.db = db
        self.redis = redis_client
        self.es = AsyncElasticsearch(ES_CONFIG["hosts"])
        self.index_name = ES_CONFIG["index_name"]

    async def ensure_index_exists(self) -> dict:
        """Ensure Elasticsearch index exists with proper mapping"""
        if not await self.es.indices.exists(index=self.index_name):
            await self.es.indices.create(
                index=self.index_name,
                settings=ES_CONFIG["settings"],
                mappings=ES_CONFIG["mappings"],
            )

    async def index_product(self, product_data: Dict[str, Any]) -> bool:
        """Index a single product"""
        try:
            # Prepare document for indexing
            doc = await self._prepare_product_document(product_data)

            # Index document
            await self.es.index(
                index=self.index_name, id=product_data["id"], document=doc
            )

            return True

        except Exception as e:
            print(f"Error indexing product {product_data.get('id')}: {e}")
            return False

    async def _prepare_product_document(
        self, product_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Prepare product document for Elasticsearch indexing"""
        doc = {
            "id": str(product_data["id"]),
            "sku": product_data["sku"],
            "name": product_data["name"],
            "description": product_data.get("description", ""),
            "short_description": product_data.get("short_description", ""),
            "price": float(product_data["base_price"]),
            "compare_at_price": float(product_data.get("compare_at_price", 0))
            if product_data.get("compare_at_price")
            else None,
            "cost_price": float(product_data.get("cost_price", 0))
            if product_data.get("cost_price")
            else None,
            "status": product_data["status"],
            "product_type": product_data["product_type"],
            "is_visible": product_data["is_visible"],
            "is_featured": product_data["is_featured"],
            "inventory_quantity": product_data["inventory_quantity"],
            "track_inventory": product_data["track_inventory"],
            "weight": float(product_data.get("weight", 0))
            if product_data.get("weight")
            else None,
            "dimensions": product_data.get("dimensions"),
            "tags": product_data.get("tags", []),
            "created_at": product_data["created_at"].isoformat()
            if product_data.get("created_at")
            else None,
            "updated_at": product_data["updated_at"].isoformat()
            if product_data.get("updated_at")
            else None,
            "published_at": product_data.get("published_at").isoformat()
            if product_data.get("published_at")
            else None,
        }

        # Add category information
        if product_data.get("category"):
            doc["category"] = {
                "id": str(product_data["category"]["id"]),
                "name": product_data["category"]["name"],
                "slug": product_data["category"]["slug"],
                "hierarchy": self._build_category_hierarchy(product_data["category"]),
            }

        # Add brand information
        if product_data.get("brand"):
            doc["brand"] = {
                "id": str(product_data["brand"]["id"]),
                "name": product_data["brand"]["name"],
                "slug": product_data["brand"]["slug"],
            }

        # Add attributes
        if product_data.get("attributes"):
            doc["attributes"] = [
                {
                    "name": attr["name"],
                    "value": attr["value"],
                    "display_value": attr.get("display_value", attr["value"]),
                }
                for attr in product_data["attributes"]
            ]

        # Add images
        if product_data.get("images"):
            doc["images"] = [
                {
                    "url": img["url"],
                    "alt": img.get("alt", ""),
                    "is_primary": img.get("is_primary", False),
                }
                for img in product_data["images"]
            ]

        # Add popularity metrics
        popularity = await self._get_product_popularity(product_data["id"])
        if popularity:
            doc["rating"] = {
                "average": float(popularity.get("rating_average", 0)),
                "count": popularity.get("rating_count", 0),
            }
            doc["sales_count"] = popularity.get("sales_count", 0)
            doc["view_count"] = popularity.get("view_count", 0)

        # Generate search keywords
        doc["search_keywords"] = self._generate_search_keywords(doc)

        # Generate autocomplete suggestions
        doc["suggest"] = {
            "input": [
                product_data["name"],
                product_data["sku"],
                *product_data.get("tags", []),
            ],
            "weight": self._calculate_suggestion_weight(doc),
        }

        return doc

    def _build_category_hierarchy(self, category: Dict[str, Any]) -> List[str]:
        """Build category hierarchy for faceted search"""
        hierarchy = []
        current = category

        while current:
            hierarchy.insert(0, current["name"])
            current = current.get("parent")

        return hierarchy

    async def _get_product_popularity(
        self, product_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get product popularity metrics"""
        cache_key = f"product_popularity:{product_id}"
        cached = await self.redis.get(cache_key)

        if cached:
            return json.loads(cached)

        # Query from database
        query = select(ProductPopularity).where(
            ProductPopularity.product_id == product_id
        )
        result = await self.db.execute(query)
        popularity = result.scalar_one_or_none()

        if popularity:
            data = {
                "view_count": popularity.view_count,
                "sales_count": popularity.purchase_count,
                "rating_average": float(popularity.popularity_score),
                "rating_count": popularity.view_count,  # Approximation
            }

            # Cache for 1 hour
            await self.redis.setex(cache_key, 3600, json.dumps(data))
            return data

        return None

    def _generate_search_keywords(self, doc: Dict[str, Any]) -> str:
        """Generate additional search keywords"""
        keywords = []

        # Add name and description
        keywords.append(doc.get("name", ""))
        keywords.append(doc.get("description", ""))

        # Add category names
        if doc.get("category"):
            keywords.extend(doc["category"].get("hierarchy", []))

        # Add brand name
        if doc.get("brand"):
            keywords.append(doc["brand"]["name"])

        # Add attribute values
        if doc.get("attributes"):
            for attr in doc["attributes"]:
                keywords.append(attr["display_value"])

        # Add tags
        keywords.extend(doc.get("tags", []))

        return " ".join(filter(None, keywords))

    def _calculate_suggestion_weight(self, doc: Dict[str, Any]) -> int:
        """Calculate suggestion weight for autocomplete"""
        weight = 1

        # Boost featured products
        if doc.get("is_featured"):
            weight += 5

        # Boost by popularity
        if doc.get("view_count", 0) > 100:
            weight += 3

        # Boost by availability
        if doc.get("inventory_quantity", 0) > 0:
            weight += 2

        return min(weight, 10)  # Cap at 10

    async def search_products(self, request: SearchRequest) -> SearchResponse:
        """Advanced product search with filters and facets"""
        start_time = datetime.utcnow()

        # Build Elasticsearch query
        query = await self._build_search_query(request)

        # Execute search
        try:
            response = await self.es.search(
                index=self.index_name,
                body=query,
                from_=(request.page - 1) * request.size,
                size=request.size,
            )

            # Process results
            products = []
            for hit in response["hits"]["hits"]:
                product = hit["_source"]
                product["score"] = hit["_score"]

                # Add highlights if enabled
                if request.highlight and "highlight" in hit:
                    product["highlights"] = hit["highlight"]

                products.append(product)

            # Process facets
            facets = {}
            if request.include_facets and "aggregations" in response:
                facets = await self._process_facets(response["aggregations"])

            # Generate suggestions
            suggestions = []
            if request.include_suggestions and request.query:
                suggestions = await self._generate_suggestions(request.query)

            # Calculate execution time
            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            # Log search query
            await self._log_search_query(
                request, response["hits"]["total"]["value"], execution_time
            )

            return SearchResponse(
                query=request.query,
                total=response["hits"]["total"]["value"],
                page=request.page,
                size=request.size,
                pages=(response["hits"]["total"]["value"] + request.size - 1)
                // request.size,
                execution_time_ms=execution_time,
                products=products,
                facets=facets if request.include_facets else None,
                suggestions=suggestions if request.include_suggestions else None,
            )

        except Exception as e:
            print(f"Search error: {e}")
            raise HTTPException(status_code=500, detail="Search service unavailable")

    async def _build_search_query(self, request: SearchRequest) -> Dict[str, Any]:
        """Build Elasticsearch query from search request"""
        query = {
            "query": {"bool": {"must": [], "filter": [], "should": []}},
            "sort": [],
            "aggs": {},
        }

        # Add text search query
        if request.query:
            text_query = self._build_text_query(request.query, request.scope)
            query["query"]["bool"]["must"].append(text_query)
        else:
            query["query"]["bool"]["must"].append({"match_all": {}})

        # Add filters
        if request.filters:
            for field, filter_value in request.filters.items():
                filter_query = self._build_filter_query(field, filter_value)
                if filter_query:
                    query["query"]["bool"]["filter"].append(filter_query)

        # Add default filters
        query["query"]["bool"]["filter"].extend(
            [{"term": {"is_visible": True}}, {"term": {"status": "active"}}]
        )

        # Add sorting
        sort_config = self._build_sort_config(request.sort)
        query["sort"] = sort_config

        # Add facets/aggregations
        if request.include_facets:
            facet_aggs = await self._build_facet_aggregations(request.facets)
            query["aggs"].update(facet_aggs)

        # Add highlighting
        if request.highlight and request.query:
            query["highlight"] = {
                "fields": {"name": {}, "description": {}, "search_keywords": {}},
                "pre_tags": ["<mark>"],
                "post_tags": ["</mark>"],
            }

        return query

    def _build_text_query(self, query_text: str, scope: SearchScope) -> Dict[str, Any]:
        """Build text search query based on scope"""
        if scope == SearchScope.ALL:
            return {
                "multi_match": {
                    "query": query_text,
                    "fields": [
                        "name^3",
                        "name.autocomplete^2",
                        "sku^2",
                        "description",
                        "short_description^1.5",
                        "search_keywords",
                        "category.name",
                        "brand.name",
                        "tags",
                        "attributes.display_value",
                    ],
                    "type": "best_fields",
                    "fuzziness": "AUTO",
                    "operator": "and",
                }
            }
        elif scope == SearchScope.NAME:
            return {
                "multi_match": {
                    "query": query_text,
                    "fields": ["name^2", "name.autocomplete"],
                    "fuzziness": "AUTO",
                }
            }
        elif scope == SearchScope.SKU:
            return {"term": {"sku": {"value": query_text.upper(), "boost": 3.0}}}
        elif scope == SearchScope.DESCRIPTION:
            return {
                "multi_match": {
                    "query": query_text,
                    "fields": ["description", "short_description"],
                    "type": "phrase",
                }
            }
        elif scope == SearchScope.CATEGORY:
            return {
                "nested": {
                    "path": "category",
                    "query": {
                        "multi_match": {
                            "query": query_text,
                            "fields": ["category.name", "category.hierarchy"],
                        }
                    },
                }
            }
        elif scope == SearchScope.BRAND:
            return {
                "nested": {
                    "path": "brand",
                    "query": {"match": {"brand.name": query_text}},
                }
            }
        else:
            return {"match_all": {}}

    def _build_filter_query(
        self, field: str, filter_value: Any
    ) -> Optional[Dict[str, Any]]:
        """Build filter query for specific field"""
        if field == "price_range":
            min_price, max_price = filter_value.get("min", 0), filter_value.get("max")
            range_filter = {"range": {"price": {"gte": min_price}}}
            if max_price:
                range_filter["range"]["price"]["lte"] = max_price
            return range_filter

        elif field == "category_id":
            return {
                "nested": {
                    "path": "category",
                    "query": {"term": {"category.id": str(filter_value)}},
                }
            }

        elif field == "brand_id":
            return {
                "nested": {
                    "path": "brand",
                    "query": {"term": {"brand.id": str(filter_value)}},
                }
            }

        elif field in ["status", "product_type"]:
            return {"term": {field: filter_value}}

        elif field in ["is_featured", "is_visible", "track_inventory"]:
            return {"term": {field: bool(filter_value)}}

        elif field == "tags":
            if isinstance(filter_value, list):
                return {"terms": {"tags": filter_value}}
            else:
                return {"term": {"tags": filter_value}}

        elif field == "attributes":
            # Handle attribute filters
            attribute_filters = []
            for attr_name, attr_value in filter_value.items():
                attribute_filters.append(
                    {
                        "nested": {
                            "path": "attributes",
                            "query": {
                                "bool": {
                                    "must": [
                                        {"term": {"attributes.name": attr_name}},
                                        {"term": {"attributes.value": attr_value}},
                                    ]
                                }
                            },
                        }
                    }
                )

            if len(attribute_filters) == 1:
                return attribute_filters[0]
            else:
                return {"bool": {"must": attribute_filters}}

        elif field == "inventory_available":
            if filter_value:
                return {"range": {"inventory_quantity": {"gt": 0}}}
            else:
                return {"term": {"inventory_quantity": 0}}

        return None

    def _build_sort_config(self, sort_option: SortOption) -> List[Dict[str, Any]]:
        """Build sort configuration"""
        if sort_option == SortOption.RELEVANCE:
            return ["_score"]
        elif sort_option == SortOption.PRICE_ASC:
            return [{"price": {"order": "asc"}}]
        elif sort_option == SortOption.PRICE_DESC:
            return [{"price": {"order": "desc"}}]
        elif sort_option == SortOption.NAME_ASC:
            return [{"name.keyword": {"order": "asc"}}]
        elif sort_option == SortOption.NAME_DESC:
            return [{"name.keyword": {"order": "desc"}}]
        elif sort_option == SortOption.NEWEST:
            return [{"created_at": {"order": "desc"}}]
        elif sort_option == SortOption.OLDEST:
            return [{"created_at": {"order": "asc"}}]
        elif sort_option == SortOption.POPULARITY:
            return [{"view_count": {"order": "desc"}}, "_score"]
        elif sort_option == SortOption.RATING:
            return [{"rating.average": {"order": "desc"}}, "_score"]
        elif sort_option == SortOption.AVAILABILITY:
            return [{"inventory_quantity": {"order": "desc"}}, "_score"]
        else:
            return ["_score"]

    async def _build_facet_aggregations(
        self, requested_facets: Optional[List[str]]
    ) -> Dict[str, Any]:
        """Build facet aggregations"""
        aggregations = {}

        # Get active facets from database
        facets_query = select(SearchFacet).where(SearchFacet.is_active)
        if requested_facets:
            facets_query = facets_query.where(SearchFacet.name.in_(requested_facets))

        result = await self.db.execute(facets_query)
        facets = result.scalars().all()

        for facet in facets:
            if facet.facet_type == FacetType.TERMS:
                aggregations[facet.name] = {
                    "terms": {
                        "field": facet.field_name,
                        "size": facet.max_values,
                        "min_doc_count": facet.min_doc_count,
                    }
                }
            elif facet.facet_type == FacetType.RANGE:
                config = facet.configuration or {}
                aggregations[facet.name] = {
                    "range": {
                        "field": facet.field_name,
                        "ranges": config.get(
                            "ranges",
                            [
                                {"to": 50},
                                {"from": 50, "to": 150},
                                {"from": 150, "to": 500},
                                {"from": 500},
                            ],
                        ),
                    }
                }
            elif facet.facet_type == FacetType.HISTOGRAM:
                config = facet.configuration or {}
                aggregations[facet.name] = {
                    "histogram": {
                        "field": facet.field_name,
                        "interval": config.get("interval", 10),
                    }
                }
            elif facet.facet_type == FacetType.NESTED:
                aggregations[facet.name] = {
                    "nested": {"path": facet.configuration.get("path", "")},
                    "aggs": {
                        "values": {
                            "terms": {
                                "field": facet.field_name,
                                "size": facet.max_values,
                            }
                        }
                    },
                }

        return aggregations

    async def _process_facets(self, aggregations: Dict[str, Any]) -> Dict[str, Any]:
        """Process facet results from Elasticsearch response"""
        facets = {}

        for facet_name, facet_data in aggregations.items():
            if "buckets" in facet_data:
                # Terms facet
                facets[facet_name] = [
                    {"value": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in facet_data["buckets"]
                ]
            elif "values" in facet_data and "buckets" in facet_data["values"]:
                # Nested facet
                facets[facet_name] = [
                    {"value": bucket["key"], "count": bucket["doc_count"]}
                    for bucket in facet_data["values"]["buckets"]
                ]

        return facets

    async def _generate_suggestions(self, query: str) -> List[str]:
        """Generate search suggestions using Elasticsearch"""
        try:
            response = await self.es.search(
                index=self.index_name,
                body={
                    "suggest": {
                        "product_suggest": {
                            "prefix": query,
                            "completion": {"field": "suggest", "size": 5},
                        }
                    }
                },
            )

            suggestions = []
            for option in response["suggest"]["product_suggest"][0]["options"]:
                suggestions.extend(option["_source"]["suggest"]["input"])

            # Remove duplicates and return unique suggestions
            return list(set(suggestions))[:5]

        except Exception as e:
            print(f"Error generating suggestions: {e}")
            return []

    async def _log_search_query(
        self, request: SearchRequest, results_count: int, execution_time: int
    ):
        """Log search query for analytics"""
        search_query = SearchQuery(
            query_text=request.query or "",
            filters=request.filters,
            sort_by=request.sort.value,
            results_count=results_count,
            execution_time_ms=execution_time,
        )

        self.db.add(search_query)
        # Don't await commit to avoid slowing down search response

    async def autocomplete(self, request: AutocompleteRequest) -> AutocompleteResponse:
        """Product autocomplete search"""
        start_time = datetime.utcnow()

        suggestions = []

        try:
            # Build autocomplete query
            query = {
                "suggest": {
                    "product_suggest": {
                        "prefix": request.query,
                        "completion": {"field": "suggest", "size": request.size},
                    }
                }
            }

            # Add category filter if specified
            if request.categories:
                query["suggest"]["product_suggest"]["completion"]["contexts"] = {
                    "category": request.categories
                }

            response = await self.es.search(index=self.index_name, body=query)

            # Process suggestions
            seen_suggestions = set()
            for option in response["suggest"]["product_suggest"][0]["options"]:
                source = option["_source"]

                for suggestion_text in source["suggest"]["input"]:
                    if suggestion_text.lower() not in seen_suggestions:
                        suggestions.append(
                            {
                                "text": suggestion_text,
                                "type": "product",
                                "product_id": source["id"],
                                "product_name": source["name"],
                                "score": option["_score"],
                            }
                        )
                        seen_suggestions.add(suggestion_text.lower())

                        if len(suggestions) >= request.size:
                            break

                if len(suggestions) >= request.size:
                    break

            # Sort by score
            suggestions.sort(key=lambda x: x["score"], reverse=True)

            execution_time = int(
                (datetime.utcnow() - start_time).total_seconds() * 1000
            )

            return AutocompleteResponse(
                query=request.query,
                suggestions=suggestions,
                execution_time_ms=execution_time,
            )

        except Exception as e:
            print(f"Autocomplete error: {e}")
            return AutocompleteResponse(
                query=request.query,
                suggestions=[],
                execution_time_ms=int(
                    (datetime.utcnow() - start_time).total_seconds() * 1000
                ),
            )

    async def get_recommendations(
        self, request: RecommendationRequest
    ) -> List[Dict[str, Any]]:
        """Get product recommendations"""
        try:
            query = {"query": {"bool": {"must": []}}}

            if request.recommendation_type == "related" and request.product_id:
                # Find products with similar attributes/category
                product_query = text(
                    "SELECT category_id, brand_id, tags FROM products WHERE id = :product_id"
                )
                result = await self.db.execute(
                    product_query, {"product_id": request.product_id}
                )
                product_data = result.fetchone()

                if product_data:
                    query["query"]["bool"]["should"] = [
                        {"term": {"category.id": str(product_data.category_id)}},
                        {"term": {"brand.id": str(product_data.brand_id)}}
                        if product_data.brand_id
                        else {},
                        {"terms": {"tags": product_data.tags or []}},
                    ]
                    query["query"]["bool"]["minimum_should_match"] = 1

            elif request.recommendation_type == "popular":
                query["sort"] = [{"view_count": {"order": "desc"}}]

            elif request.recommendation_type == "trending":
                # Products with high recent activity
                query["query"]["bool"]["must"].append(
                    {"range": {"created_at": {"gte": "now-30d"}}}
                )
                query["sort"] = [{"sales_count": {"order": "desc"}}]

            # Add default filters
            query["query"]["bool"]["filter"] = [
                {"term": {"is_visible": True}},
                {"term": {"status": "active"}},
            ]

            # Exclude specified products
            if request.exclude_ids:
                query["query"]["bool"]["must_not"] = [
                    {"terms": {"id": [str(pid) for pid in request.exclude_ids]}}
                ]

            response = await self.es.search(
                index=self.index_name, body=query, size=request.size
            )

            recommendations = []
            for hit in response["hits"]["hits"]:
                product = hit["_source"]
                product["recommendation_score"] = hit["_score"]
                recommendations.append(product)

            return recommendations

        except Exception as e:
            print(f"Recommendation error: {e}")
            return []


# ============================================================================
# Router Setup
# ============================================================================

router = APIRouter(prefix="/api/v1/search", tags=["Product Search v66"])


@router.post("/", response_model=SearchResponse)
async def search_products(request: SearchRequest, db: AsyncSession = Depends(get_db)):
    """Advanced product search with filters and facets"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    search_service = ElasticsearchService(db, redis_client)

    return await search_service.search_products(request)


@router.post("/autocomplete", response_model=AutocompleteResponse)
async def autocomplete_search(
    request: AutocompleteRequest, db: AsyncSession = Depends(get_db)
):
    """Product autocomplete search"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    search_service = ElasticsearchService(db, redis_client)

    return await search_service.autocomplete(request)


@router.post("/recommendations", response_model=List[Dict[str, Any]])
async def get_recommendations(
    request: RecommendationRequest, db: AsyncSession = Depends(get_db)
):
    """Get product recommendations"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    search_service = ElasticsearchService(db, redis_client)

    return await search_service.get_recommendations(request)


@router.get("/facets", response_model=List[Dict[str, Any]])
async def get_search_facets(db: AsyncSession = Depends(get_db)):
    """Get available search facets"""
    query = (
        select(SearchFacet)
        .where(SearchFacet.is_active)
        .order_by(SearchFacet.sort_order)
    )
    result = await db.execute(query)
    facets = result.scalars().all()

    return [
        {
            "name": facet.name,
            "display_name": facet.display_name,
            "field_name": facet.field_name,
            "facet_type": facet.facet_type,
            "configuration": facet.configuration,
        }
        for facet in facets
    ]


@router.post("/index/product/{product_id}", response_model=Dict[str, Any])
async def index_product(
    product_id: uuid.UUID,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Index a specific product in Elasticsearch"""
    redis_client = await aioredis.from_url("redis://localhost:6379")
    search_service = ElasticsearchService(db, redis_client)

    # Get product data from database
    product_query = text("""
        SELECT p.*, c.name as category_name, c.slug as category_slug,
               b.name as brand_name, b.slug as brand_slug
        FROM products p
        LEFT JOIN product_categories c ON p.category_id = c.id
        LEFT JOIN brands b ON p.brand_id = b.id
        WHERE p.id = :product_id
    """)

    result = await db.execute(product_query, {"product_id": product_id})
    product_data = result.fetchone()

    if not product_data:
        raise HTTPException(status_code=404, detail="Product not found")

    # Convert to dict and index
    product_dict = dict(product_data._mapping)
    success = await search_service.index_product(product_dict)

    return {
        "product_id": product_id,
        "indexed": success,
        "message": "Product indexed successfully"
        if success
        else "Failed to index product",
    }


@router.get("/analytics", response_model=SearchAnalytics)
async def get_search_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get search analytics"""
    start_date = datetime.utcnow() - timedelta(days=days)

    # Total queries
    total_queries_query = select(func.count(SearchQuery.id)).where(
        SearchQuery.created_at >= start_date
    )
    total_result = await db.execute(total_queries_query)
    total_queries = total_result.scalar()

    # Average execution time
    avg_time_query = select(func.avg(SearchQuery.execution_time_ms)).where(
        SearchQuery.created_at >= start_date
    )
    avg_result = await db.execute(avg_time_query)
    avg_execution_time = float(avg_result.scalar() or 0)

    # Popular queries
    popular_queries_query = (
        select(SearchQuery.query_text, func.count(SearchQuery.id).label("count"))
        .where(and_(SearchQuery.created_at >= start_date, SearchQuery.query_text != ""))
        .group_by(SearchQuery.query_text)
        .order_by(func.count(SearchQuery.id).desc())
        .limit(10)
    )

    popular_result = await db.execute(popular_queries_query)
    popular_queries = [
        {"query": row.query_text, "count": row.count}
        for row in popular_result.fetchall()
    ]

    # No results queries
    no_results_query = (
        select(SearchQuery.query_text)
        .where(
            and_(
                SearchQuery.created_at >= start_date,
                SearchQuery.results_count == 0,
                SearchQuery.query_text != "",
            )
        )
        .distinct()
        .limit(20)
    )

    no_results_result = await db.execute(no_results_query)
    no_results_queries = [row.query_text for row in no_results_result.fetchall()]

    return SearchAnalytics(
        total_queries=total_queries,
        avg_execution_time=avg_execution_time,
        popular_queries=popular_queries,
        no_results_queries=no_results_queries,
        top_clicked_results=[],  # Would need click tracking
        conversion_rate=0.0,  # Would need conversion tracking
    )


@router.get("/health", response_model=Dict[str, Any])
async def health_check() -> None:
    """Search service health check"""
    return {
        "status": "healthy",
        "service": "product_search_v66",
        "version": "66.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "features": [
            "elasticsearch_search",
            "faceted_search",
            "autocomplete",
            "recommendations",
            "analytics",
            "advanced_filtering",
            "multi_language_support",
        ],
    }
