"""Natural Language Processing & Conversational AI Assistant - CC02 v75.0 Day 20."""

from __future__ import annotations

import asyncio
import json
import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import nltk
import numpy as np
from pydantic import BaseModel, Field

from ..sdk.mobile_sdk_core import MobileERPSDK
from .ai_intelligence_engine import AIIntelligenceEngine


class IntentType(str, Enum):
    """Types of user intents."""
    GREETING = "greeting"
    QUESTION = "question"
    REQUEST = "request"
    COMMAND = "command"
    COMPLAINT = "complaint"
    COMPLIMENT = "compliment"
    HELP = "help"
    NAVIGATION = "navigation"
    DATA_QUERY = "data_query"
    REPORT_REQUEST = "report_request"
    TASK_CREATION = "task_creation"
    SYSTEM_STATUS = "system_status"
    GOODBYE = "goodbye"


class EntityType(str, Enum):
    """Named entity types."""
    PERSON = "person"
    ORGANIZATION = "organization"
    LOCATION = "location"
    DATE = "date"
    TIME = "time"
    MONEY = "money"
    PERCENTAGE = "percentage"
    PRODUCT = "product"
    CUSTOMER = "customer"
    ORDER = "order"
    INVOICE = "invoice"
    EMPLOYEE = "employee"
    DEPARTMENT = "department"


class ConversationState(str, Enum):
    """Conversation flow states."""
    INITIAL = "initial"
    GATHERING_INFO = "gathering_info"
    CONFIRMING = "confirming"
    EXECUTING = "executing"
    COMPLETED = "completed"
    ERROR = "error"


class ResponseType(str, Enum):
    """Types of AI responses."""
    TEXT = "text"
    QUICK_REPLY = "quick_reply"
    CARD = "card"
    LIST = "list"
    CHART = "chart"
    TABLE = "table"
    ACTION = "action"
    FORM = "form"


class UserIntent(BaseModel):
    """Parsed user intent from natural language."""
    intent_type: IntentType
    confidence_score: float
    entities: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Intent-specific data
    query_parameters: Dict[str, Any] = Field(default_factory=dict)
    action_parameters: Dict[str, Any] = Field(default_factory=dict)
    
    # Context
    raw_text: str
    processed_text: str
    language: str = "en"
    
    # Metadata
    parsed_at: datetime = Field(default_factory=datetime.now)


class ConversationContext(BaseModel):
    """Conversation context and state management."""
    session_id: str
    user_id: str
    
    # Conversation state
    state: ConversationState = ConversationState.INITIAL
    current_intent: Optional[IntentType] = None
    
    # Context variables
    variables: Dict[str, Any] = Field(default_factory=dict)
    entities: Dict[str, Any] = Field(default_factory=dict)
    
    # Multi-turn conversation
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    pending_clarifications: List[str] = Field(default_factory=list)
    
    # Business context
    current_task: Optional[Dict[str, Any]] = None
    workspace: Optional[str] = None
    permissions: Set[str] = Field(default_factory=set)
    
    # Timing
    created_at: datetime = Field(default_factory=datetime.now)
    last_interaction: datetime = Field(default_factory=datetime.now)
    expires_at: datetime = Field(default_factory=lambda: datetime.now() + timedelta(hours=2))


class AIResponse(BaseModel):
    """AI assistant response."""
    response_id: str
    session_id: str
    
    # Response content
    response_type: ResponseType
    text: str
    
    # Rich content
    quick_replies: List[str] = Field(default_factory=list)
    cards: List[Dict[str, Any]] = Field(default_factory=list)
    charts: List[Dict[str, Any]] = Field(default_factory=list)
    tables: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Actions
    suggested_actions: List[Dict[str, Any]] = Field(default_factory=list)
    system_actions: List[Dict[str, Any]] = Field(default_factory=list)
    
    # Metadata
    confidence_score: float
    processing_time_ms: float
    generated_at: datetime = Field(default_factory=datetime.now)
    
    # Follow-up
    expects_response: bool = False
    next_prompts: List[str] = Field(default_factory=list)


class KnowledgeBase(BaseModel):
    """Knowledge base entry for AI assistant."""
    entry_id: str
    title: str
    content: str
    category: str
    
    # Metadata
    keywords: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    
    # Relevance
    usage_count: int = 0
    last_used: Optional[datetime] = None
    
    # Content structure
    sections: List[Dict[str, str]] = Field(default_factory=list)
    related_entries: List[str] = Field(default_factory=list)
    
    # Access control
    required_permissions: Set[str] = Field(default_factory=set)
    
    # Versioning
    version: str = "1.0"
    created_at: datetime = Field(default_factory=datetime.now)
    updated_at: Optional[datetime] = None


class NLPProcessor:
    """Natural language processing engine."""
    
    def __init__(self):
        self.intent_patterns: Dict[IntentType, List[str]] = {}
        self.entity_patterns: Dict[EntityType, List[str]] = {}
        self._initialize_patterns()
    
    def _initialize_patterns(self) -> None:
        """Initialize NLP patterns for intent and entity recognition."""
        # Intent patterns
        self.intent_patterns = {
            IntentType.GREETING: [
                r'\b(hello|hi|hey|good morning|good afternoon|good evening)\b',
                r'\b(start|begin|ready)\b'
            ],
            IntentType.QUESTION: [
                r'\b(what|how|when|where|why|which|who)\b',
                r'\b(tell me|show me|explain|describe)\b',
                r'\?$'
            ],
            IntentType.REQUEST: [
                r'\b(please|can you|could you|would you)\b',
                r'\b(i need|i want|i would like)\b',
                r'\b(get me|find|search for)\b'
            ],
            IntentType.COMMAND: [
                r'\b(create|generate|make|build)\b',
                r'\b(delete|remove|cancel)\b',
                r'\b(update|change|modify|edit)\b',
                r'\b(send|submit|approve|reject)\b'
            ],
            IntentType.DATA_QUERY: [
                r'\b(sales|revenue|profit|customers|orders|inventory)\b',
                r'\b(report|dashboard|analytics|metrics)\b',
                r'\b(last month|this week|today|yesterday)\b'
            ],
            IntentType.HELP: [
                r'\b(help|assist|support|guide)\b',
                r'\b(how to|tutorial|instructions)\b',
                r'\b(stuck|confused|lost)\b'
            ],
            IntentType.GOODBYE: [
                r'\b(bye|goodbye|see you|farewell|exit|quit)\b',
                r'\b(thank you|thanks|that\'s all)\b'
            ]
        }
        
        # Entity patterns
        self.entity_patterns = {
            EntityType.DATE: [
                r'\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b',
                r'\b(today|yesterday|tomorrow)\b',
                r'\b(monday|tuesday|wednesday|thursday|friday|saturday|sunday)\b',
                r'\b(january|february|march|april|may|june|july|august|september|october|november|december)\b',
                r'\b(last week|this week|next week|last month|this month|next month)\b'
            ],
            EntityType.MONEY: [
                r'\$\d+(?:,\d{3})*(?:\.\d{2})?',
                r'\b\d+(?:,\d{3})*(?:\.\d{2})?\s*(?:dollars?|usd|euro?|eur)\b'
            ],
            EntityType.PERCENTAGE: [
                r'\b\d+(?:\.\d+)?%',
                r'\b\d+(?:\.\d+)?\s*percent\b'
            ],
            EntityType.EMPLOYEE: [
                r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b(?=.*(?:employee|staff|worker|manager))',
                r'\bemp\d+\b',
                r'\bemployee\s+id\s*:?\s*\w+\b'
            ],
            EntityType.CUSTOMER: [
                r'\bcustomer\s+id\s*:?\s*\w+\b',
                r'\bcust\d+\b',
                r'\bclient\s+[A-Z][a-z]+\b'
            ],
            EntityType.ORDER: [
                r'\border\s+(?:number\s*|id\s*|#\s*):?\s*\w+\b',
                r'\border\s+\w+\b',
                r'\b#\d+\b'
            ],
            EntityType.PRODUCT: [
                r'\bproduct\s+(?:id\s*|code\s*|#\s*):?\s*\w+\b',
                r'\bsku\s*:?\s*\w+\b',
                r'\bitem\s+\w+\b'
            ]
        }
    
    async def process_text(self, text: str) -> UserIntent:
        """Process natural language text and extract intent and entities."""
        # Preprocess text
        processed_text = self._preprocess_text(text)
        
        # Extract intent
        intent_type, intent_confidence = await self._extract_intent(processed_text)
        
        # Extract entities
        entities = await self._extract_entities(processed_text)
        
        # Extract query parameters
        query_params = await self._extract_query_parameters(processed_text, intent_type)
        
        return UserIntent(
            intent_type=intent_type,
            confidence_score=intent_confidence,
            entities=entities,
            query_parameters=query_params,
            raw_text=text,
            processed_text=processed_text
        )
    
    def _preprocess_text(self, text: str) -> str:
        """Preprocess input text."""
        # Convert to lowercase
        text = text.lower().strip()
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Handle contractions
        contractions = {
            "i'm": "i am",
            "you're": "you are",
            "it's": "it is",
            "that's": "that is",
            "what's": "what is",
            "where's": "where is",
            "how's": "how is",
            "i'll": "i will",
            "you'll": "you will",
            "can't": "cannot",
            "won't": "will not",
            "don't": "do not",
            "didn't": "did not",
            "shouldn't": "should not",
            "wouldn't": "would not"
        }
        
        for contraction, expansion in contractions.items():
            text = text.replace(contraction, expansion)
        
        return text
    
    async def _extract_intent(self, text: str) -> Tuple[IntentType, float]:
        """Extract user intent from processed text."""
        intent_scores = {}
        
        for intent_type, patterns in self.intent_patterns.items():
            score = 0.0
            matches = 0
            
            for pattern in patterns:
                if re.search(pattern, text, re.IGNORECASE):
                    matches += 1
                    score += 1.0
            
            if matches > 0:
                intent_scores[intent_type] = score / len(patterns)
        
        if not intent_scores:
            # Default to question if contains question words or ends with ?
            if re.search(r'\b(what|how|when|where|why|which|who)\b', text) or text.endswith('?'):
                return IntentType.QUESTION, 0.7
            else:
                return IntentType.REQUEST, 0.5
        
        # Return intent with highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        return best_intent[0], min(1.0, best_intent[1])
    
    async def _extract_entities(self, text: str) -> List[Dict[str, Any]]:
        """Extract named entities from text."""
        entities = []
        
        for entity_type, patterns in self.entity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text, re.IGNORECASE)
                for match in matches:
                    entities.append({
                        "type": entity_type.value,
                        "value": match.group(),
                        "start": match.start(),
                        "end": match.end(),
                        "confidence": 0.8
                    })
        
        return entities
    
    async def _extract_query_parameters(
        self,
        text: str,
        intent_type: IntentType
    ) -> Dict[str, Any]:
        """Extract query parameters based on intent."""
        params = {}
        
        if intent_type == IntentType.DATA_QUERY:
            # Extract time period
            if re.search(r'\b(today|this week|this month)\b', text):
                params["time_period"] = "current"
            elif re.search(r'\b(yesterday|last week|last month)\b', text):
                params["time_period"] = "previous"
            
            # Extract metrics
            metrics = []
            if re.search(r'\b(sales|revenue)\b', text):
                metrics.append("sales")
            if re.search(r'\b(customers|clients)\b', text):
                metrics.append("customers")
            if re.search(r'\b(orders|purchases)\b', text):
                metrics.append("orders")
            if re.search(r'\b(inventory|stock)\b', text):
                metrics.append("inventory")
            
            if metrics:
                params["metrics"] = metrics
        
        elif intent_type == IntentType.REPORT_REQUEST:
            # Extract report type
            if re.search(r'\b(financial|finance)\b', text):
                params["report_type"] = "financial"
            elif re.search(r'\b(sales|revenue)\b', text):
                params["report_type"] = "sales"
            elif re.search(r'\b(customer|client)\b', text):
                params["report_type"] = "customer"
        
        return params


class ConversationManager:
    """Manages conversation context and state."""
    
    def __init__(self):
        self.active_conversations: Dict[str, ConversationContext] = {}
        self.conversation_templates: Dict[str, Dict[str, Any]] = {}
        self._setup_conversation_templates()
    
    def _setup_conversation_templates(self) -> None:
        """Setup conversation flow templates."""
        self.conversation_templates = {
            "data_query": {
                "states": [
                    {"state": "initial", "message": "What data would you like to see?"},
                    {"state": "gathering_info", "message": "What time period are you interested in?"},
                    {"state": "confirming", "message": "Let me show you {metric} for {period}. Is this correct?"},
                    {"state": "executing", "message": "Retrieving data..."},
                    {"state": "completed", "message": "Here's your requested data."}
                ],
                "required_variables": ["metric", "time_period"]
            },
            "report_generation": {
                "states": [
                    {"state": "initial", "message": "What type of report do you need?"},
                    {"state": "gathering_info", "message": "What parameters should I include?"},
                    {"state": "confirming", "message": "I'll generate a {report_type} report with {parameters}. Proceed?"},
                    {"state": "executing", "message": "Generating report..."},
                    {"state": "completed", "message": "Your report is ready!"}
                ],
                "required_variables": ["report_type", "parameters"]
            }
        }
    
    async def get_or_create_context(
        self,
        session_id: str,
        user_id: str
    ) -> ConversationContext:
        """Get existing or create new conversation context."""
        if session_id in self.active_conversations:
            context = self.active_conversations[session_id]
            context.last_interaction = datetime.now()
            return context
        
        context = ConversationContext(
            session_id=session_id,
            user_id=user_id
        )
        
        self.active_conversations[session_id] = context
        return context
    
    async def update_context(
        self,
        context: ConversationContext,
        intent: UserIntent,
        response: AIResponse
    ) -> None:
        """Update conversation context with new interaction."""
        # Add to conversation history
        context.conversation_history.append({
            "timestamp": datetime.now().isoformat(),
            "user_input": intent.raw_text,
            "intent": intent.intent_type.value,
            "ai_response": response.text,
            "confidence": intent.confidence_score
        })
        
        # Update current intent
        context.current_intent = intent.intent_type
        
        # Update entities
        for entity in intent.entities:
            context.entities[entity["type"]] = entity["value"]
        
        # Update variables
        context.variables.update(intent.query_parameters)
        
        # State management
        await self._update_conversation_state(context, intent)
    
    async def _update_conversation_state(
        self,
        context: ConversationContext,
        intent: UserIntent
    ) -> None:
        """Update conversation state based on intent and context."""
        if intent.intent_type == IntentType.DATA_QUERY:
            if context.state == ConversationState.INITIAL:
                if "metrics" in intent.query_parameters and "time_period" in intent.query_parameters:
                    context.state = ConversationState.EXECUTING
                else:
                    context.state = ConversationState.GATHERING_INFO
                    if "metrics" not in intent.query_parameters:
                        context.pending_clarifications.append("What specific metrics do you want to see?")
                    if "time_period" not in intent.query_parameters:
                        context.pending_clarifications.append("What time period are you interested in?")
        
        elif intent.intent_type == IntentType.REPORT_REQUEST:
            if context.state == ConversationState.INITIAL:
                if "report_type" in intent.query_parameters:
                    context.state = ConversationState.GATHERING_INFO
                else:
                    context.pending_clarifications.append("What type of report do you need?")
    
    async def cleanup_expired_conversations(self) -> None:
        """Remove expired conversation contexts."""
        now = datetime.now()
        expired_sessions = [
            session_id for session_id, context in self.active_conversations.items()
            if context.expires_at < now
        ]
        
        for session_id in expired_sessions:
            del self.active_conversations[session_id]


class ResponseGenerator:
    """Generates AI responses based on intent and context."""
    
    def __init__(self, knowledge_base: Dict[str, KnowledgeBase]):
        self.knowledge_base = knowledge_base
        self.response_templates: Dict[IntentType, List[str]] = {}
        self._initialize_response_templates()
    
    def _initialize_response_templates(self) -> None:
        """Initialize response templates for different intents."""
        self.response_templates = {
            IntentType.GREETING: [
                "Hello! I'm your ERP AI assistant. How can I help you today?",
                "Hi there! I'm here to help you with your ERP system. What do you need?",
                "Good day! I can help you with data queries, reports, and system navigation. What would you like to do?"
            ],
            IntentType.HELP: [
                "I can help you with:\n• Data queries and analytics\n• Report generation\n• System navigation\n• Task management\n\nWhat specific area do you need help with?",
                "Here's what I can do for you:\n• Answer questions about your business data\n• Generate reports and dashboards\n• Help you navigate the system\n• Create and manage tasks\n\nWhat would you like assistance with?",
                "I'm here to assist you with the ERP system. You can ask me about sales data, customer information, inventory levels, or generate reports. What do you need help with?"
            ],
            IntentType.GOODBYE: [
                "Goodbye! Feel free to ask if you need anything else.",
                "Have a great day! I'll be here when you need assistance.",
                "Thank you for using the ERP AI assistant. See you next time!"
            ]
        }
    
    async def generate_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> AIResponse:
        """Generate AI response based on intent and context."""
        response_id = f"resp_{context.session_id}_{int(datetime.now().timestamp())}"
        
        start_time = datetime.now()
        
        # Generate response based on intent
        if intent.intent_type == IntentType.GREETING:
            response = await self._generate_greeting_response(intent, context)
        elif intent.intent_type == IntentType.DATA_QUERY:
            response = await self._generate_data_query_response(intent, context)
        elif intent.intent_type == IntentType.REPORT_REQUEST:
            response = await self._generate_report_response(intent, context)
        elif intent.intent_type == IntentType.HELP:
            response = await self._generate_help_response(intent, context)
        elif intent.intent_type == IntentType.QUESTION:
            response = await self._generate_question_response(intent, context)
        elif intent.intent_type == IntentType.GOODBYE:
            response = await self._generate_goodbye_response(intent, context)
        else:
            response = await self._generate_default_response(intent, context)
        
        processing_time = (datetime.now() - start_time).total_seconds() * 1000
        
        ai_response = AIResponse(
            response_id=response_id,
            session_id=context.session_id,
            response_type=response["type"],
            text=response["text"],
            quick_replies=response.get("quick_replies", []),
            cards=response.get("cards", []),
            charts=response.get("charts", []),
            tables=response.get("tables", []),
            suggested_actions=response.get("suggested_actions", []),
            confidence_score=response.get("confidence", 0.8),
            processing_time_ms=processing_time,
            expects_response=response.get("expects_response", False),
            next_prompts=response.get("next_prompts", [])
        )
        
        return ai_response
    
    async def _generate_greeting_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate greeting response."""
        templates = self.response_templates[IntentType.GREETING]
        text = templates[0]  # Use first template
        
        return {
            "type": ResponseType.TEXT,
            "text": text,
            "quick_replies": [
                "Show me sales data",
                "Generate a report",
                "Help me navigate",
                "System status"
            ],
            "confidence": 0.9
        }
    
    async def _generate_data_query_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate response for data queries."""
        if context.pending_clarifications:
            # Need more information
            clarification = context.pending_clarifications[0]
            return {
                "type": ResponseType.TEXT,
                "text": clarification,
                "quick_replies": self._get_clarification_options(clarification),
                "expects_response": True,
                "confidence": 0.8
            }
        
        # Generate mock data response
        metrics = intent.query_parameters.get("metrics", ["sales"])
        time_period = intent.query_parameters.get("time_period", "current")
        
        # Mock data
        data = {
            "sales": {"value": 125000, "change": "+12%"},
            "customers": {"value": 1250, "change": "+5%"},
            "orders": {"value": 450, "change": "+8%"},
            "inventory": {"value": 25000, "change": "-3%"}
        }
        
        cards = []
        for metric in metrics:
            if metric in data:
                cards.append({
                    "title": metric.title(),
                    "value": data[metric]["value"],
                    "change": data[metric]["change"],
                    "period": time_period
                })
        
        text = f"Here's your {', '.join(metrics)} data for the {time_period} period:"
        
        return {
            "type": ResponseType.CARD,
            "text": text,
            "cards": cards,
            "suggested_actions": [
                {"type": "generate_report", "label": "Generate detailed report"},
                {"type": "export_data", "label": "Export data"}
            ],
            "confidence": 0.85
        }
    
    async def _generate_report_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate response for report requests."""
        report_type = intent.query_parameters.get("report_type")
        
        if not report_type:
            return {
                "type": ResponseType.TEXT,
                "text": "What type of report would you like me to generate?",
                "quick_replies": [
                    "Financial report",
                    "Sales report",
                    "Customer report",
                    "Inventory report"
                ],
                "expects_response": True,
                "confidence": 0.8
            }
        
        # Mock report generation
        text = f"I'll generate a {report_type} report for you. This may take a few moments..."
        
        return {
            "type": ResponseType.TEXT,
            "text": text,
            "suggested_actions": [
                {"type": "view_report", "label": "View Report", "report_type": report_type},
                {"type": "schedule_report", "label": "Schedule Regular Reports"}
            ],
            "confidence": 0.9
        }
    
    async def _generate_help_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate help response."""
        templates = self.response_templates[IntentType.HELP]
        text = templates[0]
        
        return {
            "type": ResponseType.TEXT,
            "text": text,
            "quick_replies": [
                "Data queries",
                "Report generation",
                "System navigation",
                "Task management"
            ],
            "confidence": 0.9
        }
    
    async def _generate_question_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate response for general questions."""
        # Search knowledge base
        knowledge_match = await self._search_knowledge_base(intent.processed_text)
        
        if knowledge_match:
            return {
                "type": ResponseType.TEXT,
                "text": knowledge_match["content"],
                "confidence": knowledge_match["confidence"]
            }
        
        # Default response for unknown questions
        return {
            "type": ResponseType.TEXT,
            "text": "I'm not sure about that. Could you please rephrase your question or ask about specific ERP data, reports, or system functions?",
            "quick_replies": [
                "Show me help topics",
                "Data queries",
                "Generate reports"
            ],
            "confidence": 0.6
        }
    
    async def _generate_goodbye_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate goodbye response."""
        templates = self.response_templates[IntentType.GOODBYE]
        text = templates[0]
        
        return {
            "type": ResponseType.TEXT,
            "text": text,
            "confidence": 0.9
        }
    
    async def _generate_default_response(
        self,
        intent: UserIntent,
        context: ConversationContext
    ) -> Dict[str, Any]:
        """Generate default response for unhandled intents."""
        return {
            "type": ResponseType.TEXT,
            "text": "I understand you want to " + intent.intent_type.value.replace("_", " ") + ". How can I help you with that?",
            "quick_replies": [
                "Show me data",
                "Generate report",
                "Get help"
            ],
            "expects_response": True,
            "confidence": 0.5
        }
    
    def _get_clarification_options(self, clarification: str) -> List[str]:
        """Get quick reply options for clarifications."""
        if "metrics" in clarification.lower():
            return ["Sales", "Customers", "Orders", "Inventory"]
        elif "time period" in clarification.lower():
            return ["Today", "This week", "This month", "Last month"]
        elif "report type" in clarification.lower():
            return ["Financial", "Sales", "Customer", "Inventory"]
        else:
            return ["Yes", "No", "Maybe"]
    
    async def _search_knowledge_base(self, query: str) -> Optional[Dict[str, Any]]:
        """Search knowledge base for relevant information."""
        # Simple keyword-based search
        best_match = None
        best_score = 0.0
        
        query_words = set(query.lower().split())
        
        for entry in self.knowledge_base.values():
            # Calculate relevance score
            content_words = set(entry.content.lower().split())
            keyword_words = set(word.lower() for word in entry.keywords)
            
            overlap = len(query_words.intersection(content_words.union(keyword_words)))
            score = overlap / len(query_words) if query_words else 0
            
            if score > best_score and score > 0.3:  # Minimum relevance threshold
                best_score = score
                best_match = {
                    "content": entry.content,
                    "confidence": min(0.9, score)
                }
        
        return best_match


class ConversationalAIAssistant:
    """Main conversational AI assistant system."""
    
    def __init__(
        self,
        sdk: MobileERPSDK,
        ai_engine: AIIntelligenceEngine
    ):
        self.sdk = sdk
        self.ai_engine = ai_engine
        
        # Core components
        self.nlp_processor = NLPProcessor()
        self.conversation_manager = ConversationManager()
        self.knowledge_base: Dict[str, KnowledgeBase] = {}
        
        # Response generator
        self.response_generator = ResponseGenerator(self.knowledge_base)
        
        # Conversation tracking
        self.conversation_logs: List[Dict[str, Any]] = []
        
        # System metrics
        self.metrics = {
            "total_conversations": 0,
            "total_messages": 0,
            "average_response_time_ms": 0.0,
            "intent_accuracy": 0.85,
            "user_satisfaction": 4.2
        }
        
        # Setup knowledge base and start background tasks
        self._setup_knowledge_base()
        self._background_tasks: List[asyncio.Task] = []
        self._start_background_tasks()
    
    def _setup_knowledge_base(self) -> None:
        """Setup knowledge base with ERP-related information."""
        # System navigation knowledge
        navigation_entry = KnowledgeBase(
            entry_id="nav_dashboard",
            title="Dashboard Navigation",
            content="To access your dashboard, click on the 'Dashboard' tab in the main navigation. The dashboard shows key metrics, recent activities, and quick actions.",
            category="navigation",
            keywords=["dashboard", "navigation", "main", "home"],
            tags=["ui", "navigation", "basic"]
        )
        
        self.knowledge_base[navigation_entry.entry_id] = navigation_entry
        
        # Data queries knowledge
        data_query_entry = KnowledgeBase(
            entry_id="data_queries",
            title="Data Queries and Reports",
            content="You can ask me about sales data, customer information, inventory levels, and financial metrics. I can show current or historical data and generate detailed reports.",
            category="data",
            keywords=["data", "query", "sales", "customers", "inventory", "reports"],
            tags=["data", "analytics", "reports"]
        )
        
        self.knowledge_base[data_query_entry.entry_id] = data_query_entry
        
        # System features knowledge
        features_entry = KnowledgeBase(
            entry_id="system_features",
            title="ERP System Features",
            content="Our ERP system includes customer management, inventory tracking, financial reporting, order processing, and analytics. You can access these features through the main navigation or ask me for help.",
            category="features",
            keywords=["features", "crm", "inventory", "financial", "orders", "analytics"],
            tags=["system", "features", "overview"]
        )
        
        self.knowledge_base[features_entry.entry_id] = features_entry
        
        # Troubleshooting knowledge
        troubleshooting_entry = KnowledgeBase(
            entry_id="common_issues",
            title="Common Issues and Solutions",
            content="Common issues include login problems (check credentials), slow performance (clear browser cache), and data sync issues (refresh the page). Contact support if problems persist.",
            category="troubleshooting",
            keywords=["problems", "issues", "login", "slow", "sync", "support"],
            tags=["support", "troubleshooting", "help"]
        )
        
        self.knowledge_base[troubleshooting_entry.entry_id] = troubleshooting_entry
    
    def _start_background_tasks(self) -> None:
        """Start background AI assistant tasks."""
        # Conversation cleanup
        task = asyncio.create_task(self._conversation_cleanup_loop())
        self._background_tasks.append(task)
        
        # Analytics collection
        task = asyncio.create_task(self._analytics_collection_loop())
        self._background_tasks.append(task)
        
        # Knowledge base updates
        task = asyncio.create_task(self._knowledge_base_update_loop())
        self._background_tasks.append(task)
    
    async def _conversation_cleanup_loop(self) -> None:
        """Background conversation cleanup."""
        while True:
            try:
                await self.conversation_manager.cleanup_expired_conversations()
                await asyncio.sleep(300)  # Cleanup every 5 minutes
            except Exception as e:
                print(f"Error in conversation cleanup loop: {e}")
                await asyncio.sleep(300)
    
    async def _analytics_collection_loop(self) -> None:
        """Background analytics collection."""
        while True:
            try:
                await self._update_conversation_metrics()
                await asyncio.sleep(3600)  # Update hourly
            except Exception as e:
                print(f"Error in analytics collection loop: {e}")
                await asyncio.sleep(3600)
    
    async def _knowledge_base_update_loop(self) -> None:
        """Background knowledge base updates."""
        while True:
            try:
                await self._update_knowledge_base_usage()
                await asyncio.sleep(86400)  # Update daily
            except Exception as e:
                print(f"Error in knowledge base update loop: {e}")
                await asyncio.sleep(86400)
    
    async def process_message(
        self,
        session_id: str,
        user_id: str,
        message: str
    ) -> AIResponse:
        """Process user message and generate AI response."""
        start_time = datetime.now()
        
        try:
            # Get or create conversation context
            context = await self.conversation_manager.get_or_create_context(session_id, user_id)
            
            # Process natural language
            intent = await self.nlp_processor.process_text(message)
            
            # Generate response
            response = await self.response_generator.generate_response(intent, context)
            
            # Update conversation context
            await self.conversation_manager.update_context(context, intent, response)
            
            # Log conversation
            self.conversation_logs.append({
                "session_id": session_id,
                "user_id": user_id,
                "timestamp": datetime.now().isoformat(),
                "user_message": message,
                "intent": intent.intent_type.value,
                "intent_confidence": intent.confidence_score,
                "ai_response": response.text,
                "response_confidence": response.confidence_score,
                "processing_time_ms": (datetime.now() - start_time).total_seconds() * 1000
            })
            
            # Update metrics
            self.metrics["total_messages"] += 1
            
            return response
            
        except Exception as e:
            # Error response
            error_response = AIResponse(
                response_id=f"error_{session_id}_{int(datetime.now().timestamp())}",
                session_id=session_id,
                response_type=ResponseType.TEXT,
                text="I apologize, but I encountered an error processing your request. Please try again or rephrase your question.",
                confidence_score=0.5,
                processing_time_ms=(datetime.now() - start_time).total_seconds() * 1000
            )
            
            return error_response
    
    async def _update_conversation_metrics(self) -> None:
        """Update conversation analytics metrics."""
        recent_logs = [
            log for log in self.conversation_logs
            if datetime.fromisoformat(log["timestamp"]) > datetime.now() - timedelta(hours=24)
        ]
        
        if recent_logs:
            # Calculate average response time
            avg_response_time = sum(log["processing_time_ms"] for log in recent_logs) / len(recent_logs)
            self.metrics["average_response_time_ms"] = avg_response_time
            
            # Calculate intent accuracy (simplified)
            high_confidence_intents = [log for log in recent_logs if log["intent_confidence"] > 0.8]
            intent_accuracy = len(high_confidence_intents) / len(recent_logs)
            self.metrics["intent_accuracy"] = intent_accuracy
        
        # Count unique conversations
        unique_sessions = set(log["session_id"] for log in self.conversation_logs)
        self.metrics["total_conversations"] = len(unique_sessions)
    
    async def _update_knowledge_base_usage(self) -> None:
        """Update knowledge base entry usage statistics."""
        # In a real implementation, would track which knowledge base entries were used
        for entry in self.knowledge_base.values():
            if entry.last_used and (datetime.now() - entry.last_used).days < 7:
                entry.usage_count += 1
    
    async def add_knowledge_entry(
        self,
        title: str,
        content: str,
        category: str,
        keywords: List[str],
        tags: List[str] = None
    ) -> str:
        """Add new entry to knowledge base."""
        entry_id = f"kb_{len(self.knowledge_base)}_{int(datetime.now().timestamp())}"
        
        entry = KnowledgeBase(
            entry_id=entry_id,
            title=title,
            content=content,
            category=category,
            keywords=keywords,
            tags=tags or []
        )
        
        self.knowledge_base[entry_id] = entry
        return entry_id
    
    async def get_conversation_history(
        self,
        session_id: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """Get conversation history for a session."""
        session_logs = [
            log for log in self.conversation_logs
            if log["session_id"] == session_id
        ]
        
        # Sort by timestamp and limit
        session_logs.sort(key=lambda x: x["timestamp"], reverse=True)
        return session_logs[:limit]
    
    async def get_user_insights(self, user_id: str) -> Dict[str, Any]:
        """Get conversation insights for a user."""
        user_logs = [
            log for log in self.conversation_logs
            if log["user_id"] == user_id
        ]
        
        if not user_logs:
            return {"message": "No conversation history found"}
        
        # Calculate insights
        total_messages = len(user_logs)
        unique_sessions = len(set(log["session_id"] for log in user_logs))
        
        intent_distribution = {}
        for log in user_logs:
            intent = log["intent"]
            intent_distribution[intent] = intent_distribution.get(intent, 0) + 1
        
        avg_confidence = sum(log["intent_confidence"] for log in user_logs) / total_messages
        
        return {
            "user_id": user_id,
            "total_messages": total_messages,
            "unique_sessions": unique_sessions,
            "intent_distribution": intent_distribution,
            "average_intent_confidence": avg_confidence,
            "first_interaction": min(log["timestamp"] for log in user_logs),
            "last_interaction": max(log["timestamp"] for log in user_logs)
        }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get AI assistant system overview."""
        return {
            **self.metrics,
            "active_conversations": len(self.conversation_manager.active_conversations),
            "knowledge_base_entries": len(self.knowledge_base),
            "conversation_logs": len(self.conversation_logs),
            "top_intents": self._get_top_intents(),
            "recent_activity": {
                "messages_last_24h": len([
                    log for log in self.conversation_logs
                    if datetime.fromisoformat(log["timestamp"]) > datetime.now() - timedelta(days=1)
                ]),
                "new_conversations_today": len([
                    log for log in self.conversation_logs
                    if datetime.fromisoformat(log["timestamp"]).date() == datetime.now().date()
                ])
            }
        }
    
    def _get_top_intents(self) -> List[Dict[str, Any]]:
        """Get most common user intents."""
        intent_counts = {}
        for log in self.conversation_logs:
            intent = log["intent"]
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
        
        # Sort by count and return top 5
        top_intents = sorted(intent_counts.items(), key=lambda x: x[1], reverse=True)[:5]
        
        return [
            {"intent": intent, "count": count, "percentage": count / len(self.conversation_logs) * 100}
            for intent, count in top_intents
        ]