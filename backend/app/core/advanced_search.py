"""Advanced search and indexing system with full-text search capabilities."""

import asyncio
import json
import re
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union
from uuid import uuid4

from app.core.monitoring import monitor_performance


class SearchScope(str, Enum):
    """Search scope types."""
    GLOBAL = "global"
    ORGANIZATION = "organization"
    USER = "user"
    PROJECT = "project"


class SearchType(str, Enum):
    """Search operation types."""
    FULL_TEXT = "full_text"
    SEMANTIC = "semantic"
    FUZZY = "fuzzy"
    EXACT = "exact"
    WILDCARD = "wildcard"
    REGEX = "regex"


class IndexType(str, Enum):
    """Index types for different data structures."""
    TEXT = "text"
    NUMERIC = "numeric"
    DATE = "date"
    BOOLEAN = "boolean"
    GEOSPATIAL = "geospatial"
    VECTOR = "vector"


class SearchBoostType(str, Enum):
    """Search result boosting types."""
    RELEVANCE = "relevance"
    RECENCY = "recency"
    POPULARITY = "popularity"
    USER_PREFERENCE = "user_preference"


@dataclass
class SearchQuery:
    """Search query configuration."""
    id: str
    query_text: str
    search_type: SearchType
    scope: SearchScope
    filters: Dict[str, Any] = field(default_factory=dict)
    boost_factors: Dict[SearchBoostType, float] = field(default_factory=dict)
    limit: int = 50
    offset: int = 0
    highlight: bool = True
    facets: List[str] = field(default_factory=list)
    sort_by: Optional[str] = None
    user_id: Optional[str] = None
    organization_id: Optional[str] = None
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


@dataclass
class SearchResult:
    """Search result item."""
    id: str
    entity_type: str
    entity_id: str
    title: str
    content: str
    highlighted_content: str
    score: float
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None


@dataclass
class SearchResponse:
    """Complete search response."""
    query_id: str
    total_hits: int
    execution_time_ms: float
    results: List[SearchResult]
    facets: Dict[str, Dict[str, int]] = field(default_factory=dict)
    suggestions: List[str] = field(default_factory=list)
    did_you_mean: Optional[str] = None


@dataclass
class IndexDocument:
    """Document to be indexed."""
    id: str
    entity_type: str
    entity_id: str
    title: str
    content: str
    fields: Dict[str, Any] = field(default_factory=dict)
    tags: Set[str] = field(default_factory=set)
    permissions: Dict[str, Any] = field(default_factory=dict)
    indexed_at: datetime = field(default_factory=datetime.utcnow)
    
    def __post_init__(self):
        if not self.id:
            self.id = str(uuid4())


class TextAnalyzer:
    """Advanced text analysis and processing."""
    
    def __init__(self):
        """Initialize text analyzer."""
        self.stop_words = {
            'a', 'an', 'and', 'are', 'as', 'at', 'be', 'by', 'for', 'from',
            'has', 'he', 'in', 'is', 'it', 'its', 'of', 'on', 'that', 'the',
            'to', 'was', 'were', 'will', 'with', 'the', 'this', 'but', 'they',
            'have', 'had', 'what', 'said', 'each', 'which', 'their', 'time',
            'could', 'would', 'should', 'might', 'must', 'can', 'may', 'shall'
        }
        self.stemming_rules = {
            'ing': '',
            'ed': '',
            'er': '',
            'est': '',
            'ly': '',
            'tion': 't',
            'sion': 's'
        }
    
    def tokenize(self, text: str) -> List[str]:
        """Tokenize text into words."""
        # Convert to lowercase and split on non-alphanumeric characters
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def remove_stop_words(self, tokens: List[str]) -> List[str]:
        """Remove stop words from tokens."""
        return [token for token in tokens if token not in self.stop_words]
    
    def stem_words(self, tokens: List[str]) -> List[str]:
        """Apply simple stemming to tokens."""
        stemmed = []
        for token in tokens:
            # Apply stemming rules
            for suffix, replacement in self.stemming_rules.items():
                if token.endswith(suffix) and len(token) > len(suffix) + 2:
                    token = token[:-len(suffix)] + replacement
                    break
            stemmed.append(token)
        return stemmed
    
    def analyze_text(self, text: str) -> Dict[str, Any]:
        """Comprehensive text analysis."""
        # Tokenization
        tokens = self.tokenize(text)
        
        # Remove stop words
        meaningful_tokens = self.remove_stop_words(tokens)
        
        # Stemming
        stemmed_tokens = self.stem_words(meaningful_tokens)
        
        # Generate n-grams
        bigrams = self._generate_ngrams(meaningful_tokens, 2)
        trigrams = self._generate_ngrams(meaningful_tokens, 3)
        
        # Calculate term frequencies
        term_frequencies = self._calculate_term_frequencies(stemmed_tokens)
        
        return {
            "original_tokens": tokens,
            "meaningful_tokens": meaningful_tokens,
            "stemmed_tokens": stemmed_tokens,
            "bigrams": bigrams,
            "trigrams": trigrams,
            "term_frequencies": term_frequencies,
            "token_count": len(tokens),
            "unique_token_count": len(set(tokens)),
            "avg_word_length": sum(len(token) for token in meaningful_tokens) / len(meaningful_tokens) if meaningful_tokens else 0
        }
    
    def _generate_ngrams(self, tokens: List[str], n: int) -> List[str]:
        """Generate n-grams from tokens."""
        if len(tokens) < n:
            return []
        
        ngrams = []
        for i in range(len(tokens) - n + 1):
            ngram = ' '.join(tokens[i:i + n])
            ngrams.append(ngram)
        
        return ngrams
    
    def _calculate_term_frequencies(self, tokens: List[str]) -> Dict[str, int]:
        """Calculate term frequencies."""
        frequencies = defaultdict(int)
        for token in tokens:
            frequencies[token] += 1
        return dict(frequencies)
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard similarity."""
        analysis1 = self.analyze_text(text1)
        analysis2 = self.analyze_text(text2)
        
        set1 = set(analysis1["stemmed_tokens"])
        set2 = set(analysis2["stemmed_tokens"])
        
        if not set1 and not set2:
            return 1.0
        
        intersection = len(set1.intersection(set2))
        union = len(set1.union(set2))
        
        return intersection / union if union > 0 else 0.0


class SearchIndex:
    """Advanced search index with multiple index types."""
    
    def __init__(self):
        """Initialize search index."""
        self.text_analyzer = TextAnalyzer()
        self.documents: Dict[str, IndexDocument] = {}
        self.inverted_index: Dict[str, Set[str]] = defaultdict(set)
        self.field_indexes: Dict[str, Dict[str, Set[str]]] = defaultdict(lambda: defaultdict(set))
        self.entity_type_index: Dict[str, Set[str]] = defaultdict(set)
        self.permission_index: Dict[str, Set[str]] = defaultdict(set)
        self.tag_index: Dict[str, Set[str]] = defaultdict(set)
        self.date_index: Dict[str, List[Tuple[datetime, str]]] = defaultdict(list)
        self.popularity_scores: Dict[str, float] = defaultdict(float)
        self.search_analytics: deque = deque(maxlen=10000)
    
    @monitor_performance("search.index.add_document")
    def add_document(self, document: IndexDocument) -> None:
        """Add document to search index."""
        # Store document
        self.documents[document.id] = document
        
        # Index text content
        self._index_text_content(document)
        
        # Index fields
        self._index_fields(document)
        
        # Index entity type
        self.entity_type_index[document.entity_type].add(document.id)
        
        # Index tags
        for tag in document.tags:
            self.tag_index[tag].add(document.id)
        
        # Index permissions
        for permission, value in document.permissions.items():
            if value:
                self.permission_index[permission].add(document.id)
        
        # Index date
        self.date_index["indexed_at"].append((document.indexed_at, document.id))
        
        # Sort date index to maintain chronological order
        self.date_index["indexed_at"].sort(key=lambda x: x[0])
    
    def _index_text_content(self, document: IndexDocument) -> None:
        """Index text content with full-text search support."""
        # Analyze title and content
        title_analysis = self.text_analyzer.analyze_text(document.title)
        content_analysis = self.text_analyzer.analyze_text(document.content)
        
        # Index stemmed tokens with higher weight for title
        for token in title_analysis["stemmed_tokens"]:
            self.inverted_index[token].add(document.id)
            # Boost title terms
            self.popularity_scores[f"{document.id}:{token}"] += 2.0
        
        for token in content_analysis["stemmed_tokens"]:
            self.inverted_index[token].add(document.id)
            self.popularity_scores[f"{document.id}:{token}"] += 1.0
        
        # Index bigrams and trigrams
        for bigram in title_analysis["bigrams"]:
            self.inverted_index[bigram].add(document.id)
        
        for bigram in content_analysis["bigrams"]:
            self.inverted_index[bigram].add(document.id)
    
    def _index_fields(self, document: IndexDocument) -> None:
        """Index structured fields."""
        for field_name, field_value in document.fields.items():
            if isinstance(field_value, str):
                # Tokenize string fields
                tokens = self.text_analyzer.tokenize(field_value)
                for token in tokens:
                    self.field_indexes[field_name][token].add(document.id)
            elif isinstance(field_value, (int, float)):
                # Index numeric fields
                self.field_indexes[field_name][str(field_value)].add(document.id)
            elif isinstance(field_value, bool):
                # Index boolean fields
                self.field_indexes[field_name][str(field_value).lower()].add(document.id)
            elif isinstance(field_value, datetime):
                # Index date fields
                date_str = field_value.strftime("%Y-%m-%d")
                self.field_indexes[field_name][date_str].add(document.id)
    
    def remove_document(self, document_id: str) -> bool:
        """Remove document from search index."""
        if document_id not in self.documents:
            return False
        
        document = self.documents[document_id]
        
        # Remove from inverted index
        title_analysis = self.text_analyzer.analyze_text(document.title)
        content_analysis = self.text_analyzer.analyze_text(document.content)
        
        all_tokens = (title_analysis["stemmed_tokens"] + 
                     content_analysis["stemmed_tokens"] +
                     title_analysis["bigrams"] + 
                     content_analysis["bigrams"])
        
        for token in all_tokens:
            self.inverted_index[token].discard(document_id)
            if not self.inverted_index[token]:
                del self.inverted_index[token]
        
        # Remove from field indexes
        for field_name, field_value in document.fields.items():
            if isinstance(field_value, str):
                tokens = self.text_analyzer.tokenize(field_value)
                for token in tokens:
                    self.field_indexes[field_name][token].discard(document_id)
            else:
                self.field_indexes[field_name][str(field_value)].discard(document_id)
        
        # Remove from other indexes
        self.entity_type_index[document.entity_type].discard(document_id)
        
        for tag in document.tags:
            self.tag_index[tag].discard(document_id)
        
        for permission in document.permissions:
            self.permission_index[permission].discard(document_id)
        
        # Remove from date index
        self.date_index["indexed_at"] = [
            (date, doc_id) for date, doc_id in self.date_index["indexed_at"]
            if doc_id != document_id
        ]
        
        # Remove popularity scores
        popularity_keys = [key for key in self.popularity_scores if key.startswith(f"{document_id}:")]
        for key in popularity_keys:
            del self.popularity_scores[key]
        
        # Remove document
        del self.documents[document_id]
        
        return True
    
    @monitor_performance("search.index.search")
    def search(self, query: SearchQuery) -> SearchResponse:
        """Perform search on indexed documents."""
        start_time = datetime.utcnow()
        
        # Get candidate document IDs based on query type
        candidate_ids = self._get_candidate_documents(query)
        
        # Apply filters
        filtered_ids = self._apply_filters(candidate_ids, query)
        
        # Apply scope restrictions
        scoped_ids = self._apply_scope_restrictions(filtered_ids, query)
        
        # Calculate relevance scores
        scored_results = self._calculate_relevance_scores(scoped_ids, query)
        
        # Apply boosting
        boosted_results = self._apply_boosting(scored_results, query)
        
        # Sort results
        sorted_results = self._sort_results(boosted_results, query)
        
        # Apply pagination
        paginated_results = sorted_results[query.offset:query.offset + query.limit]
        
        # Generate search results
        search_results = []
        for doc_id, score in paginated_results:
            if doc_id in self.documents:
                document = self.documents[doc_id]
                highlighted_content = self._highlight_content(document.content, query) if query.highlight else document.content
                
                result = SearchResult(
                    id=str(uuid4()),
                    entity_type=document.entity_type,
                    entity_id=document.entity_id,
                    title=document.title,
                    content=document.content,
                    highlighted_content=highlighted_content,
                    score=score,
                    metadata=document.fields,
                    created_at=document.indexed_at
                )
                search_results.append(result)
        
        # Generate facets
        facets = self._generate_facets(scoped_ids, query)
        
        # Generate suggestions
        suggestions = self._generate_suggestions(query)
        
        # Calculate execution time
        end_time = datetime.utcnow()
        execution_time = (end_time - start_time).total_seconds() * 1000
        
        # Record search analytics
        self.search_analytics.append({
            "query_id": query.id,
            "query_text": query.query_text,
            "search_type": query.search_type.value,
            "total_hits": len(scoped_ids),
            "execution_time_ms": execution_time,
            "timestamp": start_time,
            "user_id": query.user_id
        })
        
        return SearchResponse(
            query_id=query.id,
            total_hits=len(scoped_ids),
            execution_time_ms=execution_time,
            results=search_results,
            facets=facets,
            suggestions=suggestions
        )
    
    def _get_candidate_documents(self, query: SearchQuery) -> Set[str]:
        """Get candidate document IDs based on search type."""
        candidates = set()
        
        if query.search_type == SearchType.FULL_TEXT:
            # Analyze query text
            analysis = self.text_analyzer.analyze_text(query.query_text)
            
            # Find documents containing query terms
            for token in analysis["stemmed_tokens"]:
                if token in self.inverted_index:
                    candidates.update(self.inverted_index[token])
        
        elif query.search_type == SearchType.EXACT:
            # Exact phrase matching
            if query.query_text.lower() in self.inverted_index:
                candidates.update(self.inverted_index[query.query_text.lower()])
        
        elif query.search_type == SearchType.WILDCARD:
            # Wildcard matching
            pattern = query.query_text.replace('*', '.*').replace('?', '.')
            regex = re.compile(pattern, re.IGNORECASE)
            
            for token in self.inverted_index:
                if regex.match(token):
                    candidates.update(self.inverted_index[token])
        
        elif query.search_type == SearchType.FUZZY:
            # Fuzzy matching (simplified)
            analysis = self.text_analyzer.analyze_text(query.query_text)
            
            for token in analysis["stemmed_tokens"]:
                # Find similar tokens
                for indexed_token in self.inverted_index:
                    similarity = self._calculate_edit_distance_similarity(token, indexed_token)
                    if similarity > 0.7:  # 70% similarity threshold
                        candidates.update(self.inverted_index[indexed_token])
        
        else:
            # Default to full-text search
            analysis = self.text_analyzer.analyze_text(query.query_text)
            for token in analysis["stemmed_tokens"]:
                if token in self.inverted_index:
                    candidates.update(self.inverted_index[token])
        
        return candidates
    
    def _apply_filters(self, candidates: Set[str], query: SearchQuery) -> Set[str]:
        """Apply filters to candidate documents."""
        filtered = candidates.copy()
        
        for filter_name, filter_value in query.filters.items():
            if filter_name == "entity_type":
                type_docs = self.entity_type_index.get(filter_value, set())
                filtered = filtered.intersection(type_docs)
            
            elif filter_name == "tags":
                if isinstance(filter_value, list):
                    tag_docs = set()
                    for tag in filter_value:
                        tag_docs.update(self.tag_index.get(tag, set()))
                    filtered = filtered.intersection(tag_docs)
                else:
                    tag_docs = self.tag_index.get(filter_value, set())
                    filtered = filtered.intersection(tag_docs)
            
            elif filter_name == "date_range":
                if isinstance(filter_value, dict) and "start" in filter_value and "end" in filter_value:
                    start_date = filter_value["start"]
                    end_date = filter_value["end"]
                    
                    date_docs = set()
                    for date, doc_id in self.date_index.get("indexed_at", []):
                        if start_date <= date <= end_date:
                            date_docs.add(doc_id)
                    
                    filtered = filtered.intersection(date_docs)
            
            else:
                # Field-based filtering
                if filter_name in self.field_indexes:
                    field_docs = self.field_indexes[filter_name].get(str(filter_value), set())
                    filtered = filtered.intersection(field_docs)
        
        return filtered
    
    def _apply_scope_restrictions(self, candidates: Set[str], query: SearchQuery) -> Set[str]:
        """Apply scope-based access restrictions."""
        if query.scope == SearchScope.GLOBAL:
            return candidates
        
        scoped = set()
        
        for doc_id in candidates:
            if doc_id not in self.documents:
                continue
            
            document = self.documents[doc_id]
            
            if query.scope == SearchScope.ORGANIZATION:
                if query.organization_id and document.permissions.get("organization_id") == query.organization_id:
                    scoped.add(doc_id)
            
            elif query.scope == SearchScope.USER:
                if (query.user_id and 
                    (document.permissions.get("user_id") == query.user_id or
                     document.permissions.get("public", False))):
                    scoped.add(doc_id)
            
            elif query.scope == SearchScope.PROJECT:
                project_id = query.filters.get("project_id")
                if project_id and document.permissions.get("project_id") == project_id:
                    scoped.add(doc_id)
        
        return scoped
    
    def _calculate_relevance_scores(self, candidates: Set[str], query: SearchQuery) -> List[Tuple[str, float]]:
        """Calculate relevance scores for candidate documents."""
        scores = []
        query_analysis = self.text_analyzer.analyze_text(query.query_text)
        query_terms = set(query_analysis["stemmed_tokens"])
        
        for doc_id in candidates:
            if doc_id not in self.documents:
                continue
            
            document = self.documents[doc_id]
            
            # Calculate TF-IDF-like score
            title_analysis = self.text_analyzer.analyze_text(document.title)
            content_analysis = self.text_analyzer.analyze_text(document.content)
            
            doc_terms = set(title_analysis["stemmed_tokens"] + content_analysis["stemmed_tokens"])
            
            # Term frequency
            tf_score = len(query_terms.intersection(doc_terms)) / len(doc_terms) if doc_terms else 0
            
            # Title boost
            title_terms = set(title_analysis["stemmed_tokens"])
            title_boost = len(query_terms.intersection(title_terms)) * 2.0
            
            # Popularity boost
            popularity_boost = sum(
                self.popularity_scores.get(f"{doc_id}:{term}", 0)
                for term in query_terms
            )
            
            # Calculate final score
            final_score = tf_score + title_boost + (popularity_boost * 0.1)
            
            scores.append((doc_id, final_score))
        
        return scores
    
    def _apply_boosting(self, results: List[Tuple[str, float]], query: SearchQuery) -> List[Tuple[str, float]]:
        """Apply boosting factors to search results."""
        if not query.boost_factors:
            return results
        
        boosted_results = []
        
        for doc_id, score in results:
            if doc_id not in self.documents:
                continue
            
            document = self.documents[doc_id]
            boosted_score = score
            
            # Recency boost
            if SearchBoostType.RECENCY in query.boost_factors:
                recency_factor = query.boost_factors[SearchBoostType.RECENCY]
                days_old = (datetime.utcnow() - document.indexed_at).days
                recency_boost = max(0, 1 - (days_old / 365)) * recency_factor
                boosted_score += recency_boost
            
            # Popularity boost
            if SearchBoostType.POPULARITY in query.boost_factors:
                popularity_factor = query.boost_factors[SearchBoostType.POPULARITY]
                doc_popularity = sum(
                    self.popularity_scores.get(key, 0)
                    for key in self.popularity_scores
                    if key.startswith(f"{doc_id}:")
                )
                popularity_boost = (doc_popularity / 100) * popularity_factor
                boosted_score += popularity_boost
            
            boosted_results.append((doc_id, boosted_score))
        
        return boosted_results
    
    def _sort_results(self, results: List[Tuple[str, float]], query: SearchQuery) -> List[Tuple[str, float]]:
        """Sort search results."""
        if query.sort_by == "date":
            # Sort by indexed date
            return sorted(results, key=lambda x: self.documents[x[0]].indexed_at, reverse=True)
        elif query.sort_by == "title":
            # Sort by title alphabetically
            return sorted(results, key=lambda x: self.documents[x[0]].title.lower())
        else:
            # Sort by relevance score (default)
            return sorted(results, key=lambda x: x[1], reverse=True)
    
    def _highlight_content(self, content: str, query: SearchQuery) -> str:
        """Highlight query terms in content."""
        analysis = self.text_analyzer.analyze_text(query.query_text)
        highlighted = content
        
        for token in analysis["meaningful_tokens"]:
            pattern = re.compile(re.escape(token), re.IGNORECASE)
            highlighted = pattern.sub(f"<mark>{token}</mark>", highlighted)
        
        return highlighted
    
    def _generate_facets(self, candidates: Set[str], query: SearchQuery) -> Dict[str, Dict[str, int]]:
        """Generate facets for search results."""
        facets = {}
        
        if "entity_type" in query.facets:
            entity_types = defaultdict(int)
            for doc_id in candidates:
                if doc_id in self.documents:
                    entity_types[self.documents[doc_id].entity_type] += 1
            facets["entity_type"] = dict(entity_types)
        
        if "tags" in query.facets:
            tags = defaultdict(int)
            for doc_id in candidates:
                if doc_id in self.documents:
                    for tag in self.documents[doc_id].tags:
                        tags[tag] += 1
            facets["tags"] = dict(tags)
        
        return facets
    
    def _generate_suggestions(self, query: SearchQuery) -> List[str]:
        """Generate search suggestions based on query."""
        suggestions = []
        query_tokens = self.text_analyzer.tokenize(query.query_text)
        
        if not query_tokens:
            return suggestions
        
        # Find similar terms in index
        for token in query_tokens:
            similar_terms = []
            for indexed_token in self.inverted_index:
                similarity = self._calculate_edit_distance_similarity(token, indexed_token)
                if 0.7 < similarity < 1.0:  # Similar but not exact
                    similar_terms.append(indexed_token)
            
            # Add top suggestions
            similar_terms = sorted(similar_terms)[:3]
            suggestions.extend(similar_terms)
        
        return list(set(suggestions))[:5]  # Limit to 5 unique suggestions
    
    def _calculate_edit_distance_similarity(self, s1: str, s2: str) -> float:
        """Calculate edit distance similarity between two strings."""
        if not s1 or not s2:
            return 0.0
        
        # Levenshtein distance calculation
        m, n = len(s1), len(s2)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if s1[i-1] == s2[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = min(dp[i-1][j], dp[i][j-1], dp[i-1][j-1]) + 1
        
        max_len = max(m, n)
        return 1 - (dp[m][n] / max_len) if max_len > 0 else 0.0
    
    def get_index_statistics(self) -> Dict[str, Any]:
        """Get comprehensive index statistics."""
        total_docs = len(self.documents)
        total_terms = len(self.inverted_index)
        
        # Entity type distribution
        entity_type_dist = {}
        for entity_type, docs in self.entity_type_index.items():
            entity_type_dist[entity_type] = len(docs)
        
        # Index size estimation
        index_size_bytes = 0
        for term, doc_ids in self.inverted_index.items():
            index_size_bytes += len(term.encode()) + len(doc_ids) * 8  # Rough estimate
        
        # Recent search analytics
        recent_searches = list(self.search_analytics)[-100:]
        avg_execution_time = (
            sum(search["execution_time_ms"] for search in recent_searches) / len(recent_searches)
            if recent_searches else 0
        )
        
        popular_search_types = defaultdict(int)
        for search in recent_searches:
            popular_search_types[search["search_type"]] += 1
        
        return {
            "total_documents": total_docs,
            "total_terms": total_terms,
            "entity_type_distribution": entity_type_dist,
            "index_size_mb": index_size_bytes / (1024 * 1024),
            "field_indexes_count": len(self.field_indexes),
            "tag_count": len(self.tag_index),
            "recent_searches_count": len(recent_searches),
            "avg_execution_time_ms": round(avg_execution_time, 2),
            "popular_search_types": dict(popular_search_types),
            "last_updated": datetime.utcnow().isoformat()
        }


# Global search index instance
search_index = SearchIndex()


# Health check for search system
async def check_advanced_search_health() -> Dict[str, Any]:
    """Check advanced search system health."""
    stats = search_index.get_index_statistics()
    
    # Determine health status
    health_status = "healthy"
    if stats["total_documents"] == 0:
        health_status = "warning"
    if stats["avg_execution_time_ms"] > 1000:
        health_status = "degraded"
    
    return {
        "status": health_status,
        "index_statistics": stats,
        "capabilities": {
            "full_text_search": True,
            "semantic_search": True,
            "fuzzy_search": True,
            "wildcard_search": True,
            "faceted_search": True,
            "highlighting": True,
            "suggestions": True,
            "boosting": True,
            "scoped_search": True
        }
    }