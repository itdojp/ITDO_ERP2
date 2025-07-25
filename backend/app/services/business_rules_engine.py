"""
CC02 v55.0 Business Rules Engine
Enterprise-grade Business Logic Management System
Day 2 of 7-day intensive backend development
"""

from typing import List, Dict, Any, Optional, Union, Callable
from uuid import UUID, uuid4
from datetime import datetime, date, timedelta
from decimal import Decimal
from enum import Enum
import json
import asyncio
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update, delete, func, and_, or_
from sqlalchemy.orm import selectinload

from app.core.database import get_db
from app.core.exceptions import BusinessRuleError, ValidationError
from app.models.business_rules import BusinessRule, RuleExecution, RuleCondition, RuleAction
from app.models.user import User
from app.services.audit_service import AuditService

class RuleType(str, Enum):
    VALIDATION = "validation"
    CALCULATION = "calculation"
    WORKFLOW = "workflow"
    NOTIFICATION = "notification"
    APPROVAL = "approval"
    AUTOMATION = "automation"

class ConditionOperator(str, Enum):
    EQUALS = "equals"
    NOT_EQUALS = "not_equals"
    GREATER_THAN = "greater_than"
    LESS_THAN = "less_than"
    GREATER_EQUAL = "greater_equal"
    LESS_EQUAL = "less_equal"
    CONTAINS = "contains"
    NOT_CONTAINS = "not_contains"
    IN = "in"
    NOT_IN = "not_in"
    IS_NULL = "is_null"
    IS_NOT_NULL = "is_not_null"
    REGEX_MATCH = "regex_match"

class ActionType(str, Enum):
    SET_FIELD = "set_field"
    CALCULATE = "calculate"
    SEND_EMAIL = "send_email"
    CREATE_TASK = "create_task"
    UPDATE_STATUS = "update_status"
    TRIGGER_WORKFLOW = "trigger_workflow"
    LOG_EVENT = "log_event"
    BLOCK_ACTION = "block_action"

@dataclass
class RuleContext:
    """Context for rule execution"""
    entity_type: str
    entity_id: UUID
    data: Dict[str, Any]
    user_id: Optional[UUID] = None
    session: Optional[AsyncSession] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    execution_id: Optional[UUID] = None

@dataclass
class RuleResult:
    """Result of rule execution"""
    rule_id: UUID
    success: bool
    message: Optional[str] = None
    actions_performed: List[Dict[str, Any]] = field(default_factory=list)
    execution_time_ms: float = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

class BusinessRulesEngine:
    """Enterprise Business Rules Engine"""
    
    def __init__(self):
        self.rule_cache: Dict[str, List[BusinessRule]] = {}
        self.condition_evaluators: Dict[str, Callable] = {}
        self.action_executors: Dict[str, Callable] = {}
        self.audit_service = AuditService()
        self._register_default_evaluators()
        self._register_default_executors()
    
    def _register_default_evaluators(self):
        """Register default condition evaluators"""
        self.condition_evaluators.update({
            ConditionOperator.EQUALS: self._evaluate_equals,
            ConditionOperator.NOT_EQUALS: self._evaluate_not_equals,
            ConditionOperator.GREATER_THAN: self._evaluate_greater_than,
            ConditionOperator.LESS_THAN: self._evaluate_less_than,
            ConditionOperator.GREATER_EQUAL: self._evaluate_greater_equal,
            ConditionOperator.LESS_EQUAL: self._evaluate_less_equal,
            ConditionOperator.CONTAINS: self._evaluate_contains,
            ConditionOperator.NOT_CONTAINS: self._evaluate_not_contains,
            ConditionOperator.IN: self._evaluate_in,
            ConditionOperator.NOT_IN: self._evaluate_not_in,
            ConditionOperator.IS_NULL: self._evaluate_is_null,
            ConditionOperator.IS_NOT_NULL: self._evaluate_is_not_null,
            ConditionOperator.REGEX_MATCH: self._evaluate_regex_match,
        })
    
    def _register_default_executors(self):
        """Register default action executors"""
        self.action_executors.update({
            ActionType.SET_FIELD: self._execute_set_field,
            ActionType.CALCULATE: self._execute_calculate,
            ActionType.SEND_EMAIL: self._execute_send_email,
            ActionType.CREATE_TASK: self._execute_create_task,
            ActionType.UPDATE_STATUS: self._execute_update_status,
            ActionType.TRIGGER_WORKFLOW: self._execute_trigger_workflow,
            ActionType.LOG_EVENT: self._execute_log_event,
            ActionType.BLOCK_ACTION: self._execute_block_action,
        })
    
    async def execute_rules(
        self,
        context: RuleContext,
        rule_type: Optional[RuleType] = None,
        entity_event: Optional[str] = None
    ) -> List[RuleResult]:
        """Execute business rules for given context"""
        
        start_time = datetime.utcnow()
        execution_id = uuid4()
        context.execution_id = execution_id
        
        try:
            # Get applicable rules
            rules = await self._get_applicable_rules(
                context.entity_type, rule_type, entity_event, context.session
            )
            
            # Execute rules in priority order
            results = []
            for rule in sorted(rules, key=lambda r: r.priority, reverse=True):
                result = await self._execute_single_rule(rule, context)
                results.append(result)
                
                # Stop execution if a blocking rule failed
                if not result.success and rule.is_blocking:
                    break
            
            # Log execution summary
            await self._log_execution_summary(execution_id, context, results)
            
            return results
            
        except Exception as e:
            await self._log_execution_error(execution_id, context, str(e))
            raise BusinessRuleError(f"Rule execution failed: {str(e)}")
    
    async def _get_applicable_rules(
        self,
        entity_type: str,
        rule_type: Optional[RuleType],
        entity_event: Optional[str],
        session: AsyncSession
    ) -> List[BusinessRule]:
        """Get rules applicable to the context"""
        
        cache_key = f"{entity_type}:{rule_type}:{entity_event}"
        
        # Check cache first
        if cache_key in self.rule_cache:
            return [rule for rule in self.rule_cache[cache_key] if rule.is_active]
        
        # Build query
        query = select(BusinessRule).options(
            selectinload(BusinessRule.conditions),
            selectinload(BusinessRule.actions)
        ).where(
            and_(
                BusinessRule.entity_type == entity_type,
                BusinessRule.is_active == True
            )
        )
        
        if rule_type:
            query = query.where(BusinessRule.rule_type == rule_type)
        
        if entity_event:
            query = query.where(BusinessRule.trigger_event == entity_event)
        
        result = await session.execute(query)
        rules = result.scalars().all()
        
        # Cache results
        self.rule_cache[cache_key] = rules
        
        return rules
    
    async def _execute_single_rule(
        self,
        rule: BusinessRule,
        context: RuleContext
    ) -> RuleResult:
        """Execute a single business rule"""
        
        start_time = datetime.utcnow()
        result = RuleResult(rule_id=rule.id, success=True)
        
        try:
            # Evaluate conditions
            conditions_met = await self._evaluate_conditions(rule.conditions, context)
            
            if not conditions_met:
                result.message = "Conditions not met"
                return result
            
            # Execute actions
            for action in rule.actions:
                action_result = await self._execute_action(action, context)
                result.actions_performed.append({
                    "action_type": action.action_type,
                    "success": action_result.get("success", True),
                    "result": action_result
                })
                
                if not action_result.get("success", True):
                    result.errors.append(f"Action {action.action_type} failed: {action_result.get('error')}")
                    if rule.is_blocking:
                        result.success = False
                        break
            
            # Calculate execution time
            execution_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            result.execution_time_ms = execution_time
            
            # Log rule execution
            await self._log_rule_execution(rule, context, result)
            
        except Exception as e:
            result.success = False
            result.errors.append(str(e))
            result.message = f"Rule execution failed: {str(e)}"
        
        return result
    
    async def _evaluate_conditions(
        self,
        conditions: List[RuleCondition],
        context: RuleContext
    ) -> bool:
        """Evaluate all conditions for a rule"""
        
        if not conditions:
            return True
        
        # Group conditions by logical operator
        and_conditions = [c for c in conditions if c.logical_operator == "AND"]
        or_conditions = [c for c in conditions if c.logical_operator == "OR"]
        
        # Evaluate AND conditions (all must be true)
        if and_conditions:
            for condition in and_conditions:
                if not await self._evaluate_single_condition(condition, context):
                    return False
        
        # Evaluate OR conditions (at least one must be true)
        if or_conditions:
            or_result = False
            for condition in or_conditions:
                if await self._evaluate_single_condition(condition, context):
                    or_result = True
                    break
            if not or_result:
                return False
        
        return True
    
    async def _evaluate_single_condition(
        self,
        condition: RuleCondition,
        context: RuleContext
    ) -> bool:
        """Evaluate a single condition"""
        
        # Get field value from context
        field_value = self._get_field_value(condition.field_name, context)
        expected_value = condition.expected_value
        
        # Get evaluator function
        evaluator = self.condition_evaluators.get(condition.operator)
        if not evaluator:
            raise BusinessRuleError(f"Unknown condition operator: {condition.operator}")
        
        return evaluator(field_value, expected_value)
    
    def _get_field_value(self, field_path: str, context: RuleContext) -> Any:
        """Get field value from context data using dot notation"""
        
        parts = field_path.split('.')
        value = context.data
        
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        
        return value
    
    async def _execute_action(
        self,
        action: RuleAction,
        context: RuleContext
    ) -> Dict[str, Any]:
        """Execute a single action"""
        
        executor = self.action_executors.get(action.action_type)
        if not executor:
            return {"success": False, "error": f"Unknown action type: {action.action_type}"}
        
        try:
            return await executor(action, context)
        except Exception as e:
            return {"success": False, "error": str(e)}
    
    # Condition Evaluators
    def _evaluate_equals(self, field_value: Any, expected_value: Any) -> bool:
        return field_value == expected_value
    
    def _evaluate_not_equals(self, field_value: Any, expected_value: Any) -> bool:
        return field_value != expected_value
    
    def _evaluate_greater_than(self, field_value: Any, expected_value: Any) -> bool:
        try:
            return float(field_value) > float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_less_than(self, field_value: Any, expected_value: Any) -> bool:
        try:
            return float(field_value) < float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_greater_equal(self, field_value: Any, expected_value: Any) -> bool:
        try:
            return float(field_value) >= float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_less_equal(self, field_value: Any, expected_value: Any) -> bool:
        try:
            return float(field_value) <= float(expected_value)
        except (ValueError, TypeError):
            return False
    
    def _evaluate_contains(self, field_value: Any, expected_value: Any) -> bool:
        if field_value is None:
            return False
        return str(expected_value).lower() in str(field_value).lower()
    
    def _evaluate_not_contains(self, field_value: Any, expected_value: Any) -> bool:
        return not self._evaluate_contains(field_value, expected_value)
    
    def _evaluate_in(self, field_value: Any, expected_value: Any) -> bool:
        if isinstance(expected_value, str):
            expected_value = expected_value.split(',')
        return field_value in expected_value
    
    def _evaluate_not_in(self, field_value: Any, expected_value: Any) -> bool:
        return not self._evaluate_in(field_value, expected_value)
    
    def _evaluate_is_null(self, field_value: Any, expected_value: Any) -> bool:
        return field_value is None
    
    def _evaluate_is_not_null(self, field_value: Any, expected_value: Any) -> bool:
        return field_value is not None
    
    def _evaluate_regex_match(self, field_value: Any, expected_value: Any) -> bool:
        import re
        if field_value is None:
            return False
        try:
            return bool(re.match(expected_value, str(field_value)))
        except re.error:
            return False
    
    # Action Executors
    async def _execute_set_field(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Set field value in context data"""
        
        field_path = action.action_data.get('field_name')
        new_value = action.action_data.get('value')
        
        if not field_path:
            return {"success": False, "error": "field_name is required"}
        
        # Update context data
        self._set_field_value(field_path, new_value, context)
        
        return {
            "success": True,
            "field_name": field_path,
            "new_value": new_value
        }
    
    async def _execute_calculate(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Execute calculation"""
        
        formula = action.action_data.get('formula')
        target_field = action.action_data.get('target_field')
        
        if not formula or not target_field:
            return {"success": False, "error": "formula and target_field are required"}
        
        try:
            # Simple formula evaluation (would be more sophisticated in production)
            result = self._evaluate_formula(formula, context)
            self._set_field_value(target_field, result, context)
            
            return {
                "success": True,
                "formula": formula,
                "result": result,
                "target_field": target_field
            }
        except Exception as e:
            return {"success": False, "error": f"Formula evaluation failed: {str(e)}"}
    
    async def _execute_send_email(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Send email notification"""
        
        # Would integrate with email service
        recipients = action.action_data.get('recipients', [])
        subject = action.action_data.get('subject', 'Business Rule Notification')
        template = action.action_data.get('template', 'default')
        
        # Log email sending (would actually send in production)
        return {
            "success": True,
            "action": "email_sent",
            "recipients": recipients,
            "subject": subject,
            "template": template
        }
    
    async def _execute_create_task(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Create a task"""
        
        task_data = action.action_data
        
        # Would integrate with task management system
        return {
            "success": True,
            "action": "task_created",
            "task_data": task_data
        }
    
    async def _execute_update_status(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Update entity status"""
        
        new_status = action.action_data.get('status')
        if not new_status:
            return {"success": False, "error": "status is required"}
        
        # Update status in context
        self._set_field_value('status', new_status, context)
        
        return {
            "success": True,
            "action": "status_updated",
            "new_status": new_status
        }
    
    async def _execute_trigger_workflow(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Trigger workflow"""
        
        workflow_id = action.action_data.get('workflow_id')
        if not workflow_id:
            return {"success": False, "error": "workflow_id is required"}
        
        # Would integrate with workflow engine
        return {
            "success": True,
            "action": "workflow_triggered",
            "workflow_id": workflow_id
        }
    
    async def _execute_log_event(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Log event"""
        
        event_type = action.action_data.get('event_type', 'business_rule')
        message = action.action_data.get('message', 'Business rule executed')
        
        # Log to audit service
        await self.audit_service.log_event(
            event_type=event_type,
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            user_id=context.user_id,
            details={"message": message, "rule_execution_id": str(context.execution_id)}
        )
        
        return {
            "success": True,
            "action": "event_logged",
            "event_type": event_type,
            "message": message
        }
    
    async def _execute_block_action(self, action: RuleAction, context: RuleContext) -> Dict[str, Any]:
        """Block the current action"""
        
        reason = action.action_data.get('reason', 'Action blocked by business rule')
        
        raise BusinessRuleError(reason)
    
    def _set_field_value(self, field_path: str, value: Any, context: RuleContext):
        """Set field value in context data using dot notation"""
        
        parts = field_path.split('.')
        data = context.data
        
        # Navigate to the parent of the target field
        for part in parts[:-1]:
            if part not in data:
                data[part] = {}
            data = data[part]
        
        # Set the final field value
        data[parts[-1]] = value
    
    def _evaluate_formula(self, formula: str, context: RuleContext) -> Any:
        """Evaluate mathematical formula (simplified implementation)"""
        
        # Replace field references with actual values
        import re
        
        def replace_field(match):
            field_name = match.group(1)
            value = self._get_field_value(field_name, context)
            return str(value) if value is not None else '0'
        
        # Replace field references like ${field.name} with values
        expanded_formula = re.sub(r'\$\{([^}]+)\}', replace_field, formula)
        
        # Simple evaluation (would use a proper expression parser in production)
        try:
            return eval(expanded_formula, {"__builtins__": {}})
        except Exception as e:
            raise BusinessRuleError(f"Formula evaluation failed: {str(e)}")
    
    async def _log_rule_execution(self, rule: BusinessRule, context: RuleContext, result: RuleResult):
        """Log rule execution details"""
        
        if context.session:
            execution_log = RuleExecution(
                id=uuid4(),
                rule_id=rule.id,
                entity_type=context.entity_type,
                entity_id=context.entity_id,
                execution_id=context.execution_id,
                success=result.success,
                execution_time_ms=result.execution_time_ms,
                actions_performed=len(result.actions_performed),
                errors=result.errors,
                warnings=result.warnings,
                context_data=context.data,
                result_data=result.actions_performed,
                executed_by=context.user_id,
                executed_at=datetime.utcnow()
            )
            
            context.session.add(execution_log)
    
    async def _log_execution_summary(
        self,
        execution_id: UUID,
        context: RuleContext,
        results: List[RuleResult]
    ):
        """Log execution summary"""
        
        total_rules = len(results)
        successful_rules = len([r for r in results if r.success])
        total_errors = sum(len(r.errors) for r in results)
        total_time = sum(r.execution_time_ms for r in results)
        
        await self.audit_service.log_event(
            event_type="business_rules_execution",
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            user_id=context.user_id,
            details={
                "execution_id": str(execution_id),
                "total_rules": total_rules,
                "successful_rules": successful_rules,
                "failed_rules": total_rules - successful_rules,
                "total_errors": total_errors,
                "total_execution_time_ms": total_time
            }
        )
    
    async def _log_execution_error(
        self,
        execution_id: UUID,
        context: RuleContext,
        error: str
    ):
        """Log execution error"""
        
        await self.audit_service.log_event(
            event_type="business_rules_execution_error",
            entity_type=context.entity_type,
            entity_id=context.entity_id,
            user_id=context.user_id,
            details={
                "execution_id": str(execution_id),
                "error": error
            }
        )
    
    def clear_cache(self):
        """Clear rule cache"""
        self.rule_cache.clear()
    
    def register_condition_evaluator(self, operator: str, evaluator: Callable):
        """Register custom condition evaluator"""
        self.condition_evaluators[operator] = evaluator
    
    def register_action_executor(self, action_type: str, executor: Callable):
        """Register custom action executor"""
        self.action_executors[action_type] = executor

# Singleton instance
business_rules_engine = BusinessRulesEngine()

# Helper functions for easy access
async def execute_business_rules(
    entity_type: str,
    entity_id: UUID,
    data: Dict[str, Any],
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
    rule_type: Optional[RuleType] = None,
    entity_event: Optional[str] = None
) -> List[RuleResult]:
    """Execute business rules for an entity"""
    
    context = RuleContext(
        entity_type=entity_type,
        entity_id=entity_id,
        data=data,
        user_id=user_id,
        session=session
    )
    
    return await business_rules_engine.execute_rules(context, rule_type, entity_event)

async def validate_business_rules(
    entity_type: str,
    entity_id: UUID,
    data: Dict[str, Any],
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None
) -> List[RuleResult]:
    """Execute validation business rules"""
    
    return await execute_business_rules(
        entity_type, entity_id, data, user_id, session,
        rule_type=RuleType.VALIDATION
    )

async def execute_calculation_rules(
    entity_type: str,
    entity_id: UUID,
    data: Dict[str, Any],
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None
) -> List[RuleResult]:
    """Execute calculation business rules"""
    
    return await execute_business_rules(
        entity_type, entity_id, data, user_id, session,
        rule_type=RuleType.CALCULATION
    )

async def execute_workflow_rules(
    entity_type: str,
    entity_id: UUID,
    data: Dict[str, Any],
    user_id: Optional[UUID] = None,
    session: Optional[AsyncSession] = None,
    entity_event: Optional[str] = None
) -> List[RuleResult]:
    """Execute workflow business rules"""
    
    return await execute_business_rules(
        entity_type, entity_id, data, user_id, session,
        rule_type=RuleType.WORKFLOW, entity_event=entity_event
    )