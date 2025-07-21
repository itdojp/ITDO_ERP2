"""Task DataLoader for batch loading tasks."""

from typing import List, Union

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import Session

from app.models.task import Task as TaskModel


async def load_tasks_batch(
    db: Union[Session, AsyncSession], 
    task_ids: List[int]
) -> List[TaskModel]:
    """Batch load tasks by IDs."""
    if hasattr(db, 'execute'):  # AsyncSession
        result = await db.execute(
            select(TaskModel).where(TaskModel.id.in_(task_ids))
        )
        tasks = result.scalars().all()
    else:  # Session
        result = db.execute(
            select(TaskModel).where(TaskModel.id.in_(task_ids))
        )
        tasks = result.scalars().all()
    
    # Create lookup dictionary
    task_dict = {task.id: task for task in tasks}
    
    # Return tasks in the same order as requested IDs
    return [task_dict.get(task_id) for task_id in task_ids]