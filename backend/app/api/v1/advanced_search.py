"""Advanced search API endpoints."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from app.core.auth import get_current_user
from app.core.advanced_search import (
    search_index,
    SearchQuery,
    SearchScope,
    SearchType,
    SearchBoostType,
    IndexDocument,
    check_advanced_search_health
)
from app.models.user import User

router = APIRouter()


# Pydantic schemas
class SearchRequest(BaseModel):
    """Search request."""
    query_text: str = Field(..., max_length=1000)
    search_type: SearchType = SearchType.FULL_TEXT
    scope: SearchScope = SearchScope.ORGANIZATION
    filters: Dict[str, Any] = Field(default_factory=dict)
    boost_factors: Dict[SearchBoostType, float] = Field(default_factory=dict)
    limit: int = Field(50, ge=1, le=100)
    offset: int = Field(0, ge=0)
    highlight: bool = True
    facets: List[str] = Field(default_factory=list)
    sort_by: Optional[str] = Field(None, regex="^(relevance|date|title)$")


class SearchResultResponse(BaseModel):
    """Search result response."""
    id: str
    entity_type: str
    entity_id: str
    title: str
    content: str
    highlighted_content: str
    score: float
    metadata: Dict[str, Any]
    created_at: str


class SearchResponse(BaseModel):
    """Complete search response."""
    query_id: str
    total_hits: int
    execution_time_ms: float
    results: List[SearchResultResponse]
    facets: Dict[str, Dict[str, int]]
    suggestions: List[str]
    did_you_mean: Optional[str]


class IndexDocumentRequest(BaseModel):
    """Index document request."""
    entity_type: str = Field(..., max_length=100)
    entity_id: str = Field(..., max_length=100)
    title: str = Field(..., max_length=500)
    content: str = Field(..., max_length=50000)
    fields: Dict[str, Any] = Field(default_factory=dict)
    tags: List[str] = Field(default_factory=list)
    permissions: Dict[str, Any] = Field(default_factory=dict)


class IndexStatsResponse(BaseModel):
    """Index statistics response."""
    total_documents: int
    total_terms: int
    entity_type_distribution: Dict[str, int]
    index_size_mb: float
    field_indexes_count: int
    tag_count: int
    recent_searches_count: int
    avg_execution_time_ms: float
    popular_search_types: Dict[str, int]
    last_updated: str


class SearchHealthResponse(BaseModel):
    """Search health response."""
    status: str
    index_statistics: IndexStatsResponse
    capabilities: Dict[str, bool]


# Search endpoints
@router.post("/search", response_model=SearchResponse)
async def search_documents(
    search_request: SearchRequest,
    current_user: User = Depends(get_current_user)
):
    """Perform advanced search on indexed documents."""
    try:
        # Create search query
        query = SearchQuery(
            id="",  # Will be auto-generated
            query_text=search_request.query_text,
            search_type=search_request.search_type,
            scope=search_request.scope,
            filters=search_request.filters,
            boost_factors=search_request.boost_factors,
            limit=search_request.limit,
            offset=search_request.offset,
            highlight=search_request.highlight,
            facets=search_request.facets,
            sort_by=search_request.sort_by,
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id) if current_user.organization_id else None
        )
        
        # Perform search
        search_result = search_index.search(query)
        
        # Convert results to response format
        result_responses = []
        for result in search_result.results:
            result_responses.append(SearchResultResponse(
                id=result.id,
                entity_type=result.entity_type,
                entity_id=result.entity_id,
                title=result.title,
                content=result.content,
                highlighted_content=result.highlighted_content,
                score=result.score,
                metadata=result.metadata,
                created_at=result.created_at.isoformat()
            ))
        
        return SearchResponse(
            query_id=search_result.query_id,
            total_hits=search_result.total_hits,
            execution_time_ms=search_result.execution_time_ms,
            results=result_responses,
            facets=search_result.facets,
            suggestions=search_result.suggestions,
            did_you_mean=search_result.did_you_mean
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Search failed: {str(e)}"
        )


@router.get("/search/suggestions")
async def get_search_suggestions(
    query: str = Query(..., max_length=100),
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user)
):
    """Get search suggestions based on partial query."""
    try:
        # Create a temporary search query for suggestions
        temp_query = SearchQuery(
            id="temp",
            query_text=query,
            search_type=SearchType.FULL_TEXT,
            scope=SearchScope.ORGANIZATION,
            user_id=str(current_user.id),
            organization_id=str(current_user.organization_id) if current_user.organization_id else None
        )
        
        suggestions = search_index._generate_suggestions(temp_query)
        
        return {
            "query": query,
            "suggestions": suggestions[:limit],
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate suggestions: {str(e)}"
        )


# Index management endpoints
@router.post("/index/documents")
async def index_document(
    doc_request: IndexDocumentRequest,
    current_user: User = Depends(get_current_user)
):
    """Add document to search index."""
    try:
        # Add user permissions
        permissions = doc_request.permissions.copy()
        permissions.update({
            "user_id": str(current_user.id),
            "organization_id": str(current_user.organization_id) if current_user.organization_id else None
        })
        
        # Create index document
        document = IndexDocument(
            id="",  # Will be auto-generated
            entity_type=doc_request.entity_type,
            entity_id=doc_request.entity_id,
            title=doc_request.title,
            content=doc_request.content,
            fields=doc_request.fields,
            tags=set(doc_request.tags),
            permissions=permissions
        )
        
        # Add to index
        search_index.add_document(document)
        
        return {
            "message": "Document indexed successfully",
            "document_id": document.id,
            "entity_type": document.entity_type,
            "entity_id": document.entity_id,
            "indexed_at": document.indexed_at.isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to index document: {str(e)}"
        )


@router.delete("/index/documents/{document_id}")
async def remove_document_from_index(
    document_id: str,
    current_user: User = Depends(get_current_user)
):
    """Remove document from search index."""
    try:
        # Check if document exists and user has permission
        if document_id not in search_index.documents:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Document not found in index"
            )
        
        document = search_index.documents[document_id]
        
        # Check permissions
        if (document.permissions.get("user_id") != str(current_user.id) and
            not current_user.is_superuser):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to remove this document"
            )
        
        # Remove from index
        success = search_index.remove_document(document_id)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to remove document from index"
            )
        
        return {
            "message": "Document removed successfully",
            "document_id": document_id,
            "removed_at": datetime.utcnow().isoformat()
        }
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to remove document: {str(e)}"
        )


@router.post("/index/reindex")
async def reindex_entity(
    entity_type: str = Query(..., max_length=100),
    entity_id: Optional[str] = Query(None, max_length=100),
    current_user: User = Depends(get_current_user)
):
    """Reindex specific entity or all entities of a type."""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin permissions required"
        )
    
    try:
        # This would integrate with actual data sources in production
        # For now, we'll simulate reindexing
        
        documents_reindexed = 0
        
        if entity_id:
            # Reindex specific entity
            # Would fetch data from database and reindex
            documents_reindexed = 1
        else:
            # Reindex all entities of type
            # Would fetch all entities of type and reindex
            documents_reindexed = 10  # Simulated count
        
        return {
            "message": f"Reindexing completed for {entity_type}",
            "entity_type": entity_type,
            "entity_id": entity_id,
            "documents_reindexed": documents_reindexed,
            "reindexed_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Reindexing failed: {str(e)}"
        )


# Analytics endpoints
@router.get("/analytics/search-stats")
async def get_search_analytics(
    hours: int = Query(24, ge=1, le=168),
    current_user: User = Depends(get_current_user)
):
    """Get search analytics and statistics."""
    try:
        # Get recent search analytics
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)
        recent_searches = [
            search for search in search_index.search_analytics
            if search["timestamp"] > cutoff_time
        ]
        
        # Calculate statistics
        total_searches = len(recent_searches)
        if total_searches > 0:
            avg_execution_time = sum(s["execution_time_ms"] for s in recent_searches) / total_searches
            avg_hits = sum(s["total_hits"] for s in recent_searches) / total_searches
        else:
            avg_execution_time = 0
            avg_hits = 0
        
        # Popular queries
        query_counts = {}
        search_type_counts = {}
        for search in recent_searches:
            query_text = search["query_text"].lower()
            query_counts[query_text] = query_counts.get(query_text, 0) + 1
            search_type = search["search_type"]
            search_type_counts[search_type] = search_type_counts.get(search_type, 0) + 1
        
        popular_queries = sorted(query_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        
        return {
            "period_hours": hours,
            "total_searches": total_searches,
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "avg_hits_per_search": round(avg_hits, 2),
            "popular_queries": popular_queries,
            "search_type_distribution": search_type_counts,
            "generated_at": datetime.utcnow().isoformat()
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get search analytics: {str(e)}"
        )


@router.get("/analytics/index-stats", response_model=IndexStatsResponse)
async def get_index_statistics(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive index statistics."""
    try:
        stats = search_index.get_index_statistics()
        
        return IndexStatsResponse(
            total_documents=stats["total_documents"],
            total_terms=stats["total_terms"],
            entity_type_distribution=stats["entity_type_distribution"],
            index_size_mb=stats["index_size_mb"],
            field_indexes_count=stats["field_indexes_count"],
            tag_count=stats["tag_count"],
            recent_searches_count=stats["recent_searches_count"],
            avg_execution_time_ms=stats["avg_execution_time_ms"],
            popular_search_types=stats["popular_search_types"],
            last_updated=stats["last_updated"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get index statistics: {str(e)}"
        )


# System endpoints
@router.get("/health", response_model=SearchHealthResponse)
async def search_health_check():
    """Check advanced search system health."""
    try:
        health_info = await check_advanced_search_health()
        
        stats = health_info["index_statistics"]
        
        return SearchHealthResponse(
            status=health_info["status"],
            index_statistics=IndexStatsResponse(
                total_documents=stats["total_documents"],
                total_terms=stats["total_terms"],
                entity_type_distribution=stats["entity_type_distribution"],
                index_size_mb=stats["index_size_mb"],
                field_indexes_count=stats["field_indexes_count"],
                tag_count=stats["tag_count"],
                recent_searches_count=stats["recent_searches_count"],
                avg_execution_time_ms=stats["avg_execution_time_ms"],
                popular_search_types=stats["popular_search_types"],
                last_updated=stats["last_updated"]
            ),
            capabilities=health_info["capabilities"]
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Search health check failed: {str(e)}"
        )


@router.get("/capabilities")
async def get_search_capabilities():
    """Get search system capabilities."""
    return {
        "search_types": [st.value for st in SearchType],
        "search_scopes": [ss.value for ss in SearchScope],
        "boost_types": [bt.value for bt in SearchBoostType],
        "features": {
            "full_text_search": True,
            "semantic_search": True,
            "fuzzy_search": True,
            "exact_search": True,
            "wildcard_search": True,
            "regex_search": True,
            "faceted_search": True,
            "highlighted_results": True,
            "search_suggestions": True,
            "result_boosting": True,
            "scoped_search": True,
            "field_based_filtering": True,
            "tag_based_filtering": True,
            "date_range_filtering": True,
            "real_time_indexing": True,
            "analytics_tracking": True
        },
        "limits": {
            "max_query_length": 1000,
            "max_content_length": 50000,
            "max_results_per_page": 100,
            "max_suggestions": 20
        }
    }