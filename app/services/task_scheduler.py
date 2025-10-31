from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.interval import IntervalTrigger
from apscheduler.events import EVENT_JOB_ERROR, EVENT_JOB_EXECUTED

from .ai_engine import AIEngine


class TaskScheduler:
    """
    TaskScheduler orchestrates automated task management using APScheduler.

    Features:
    - Recurring task scheduling (interval/cron) and one-off jobs
    - Deadline monitoring and overdue escalation
    - Dynamic priority recalculation
    - AI-powered task suggestions via AIEngine

    Expected task schema (example):
    {
        "id": str,
        "title": str,
        "description": str,
        "priority": int,               # 1 (highest) ... 5 (lowest)
        "deadline": Optional[datetime],
        "estimated_duration": Optional[int],  # minutes
        "status": str,                 # e.g., "pending", "in_progress", "done"
        "tags": List[str],
        "assignee": Optional[str],
        "metadata": Dict[str, Any],
    }
    """

    def __init__(self, ai_engine: Optional[AIEngine] = None, timezone: Optional[str] = None) -> None:
        self.scheduler = BackgroundScheduler(timezone=timezone)
        self.ai_engine = ai_engine or AIEngine()
        self._started = False

        # In-memory task registry (replace with DB/service integration as needed)
        self.tasks: Dict[str, Dict[str, Any]] = {}

        # Attach listeners
        self.scheduler.add_listener(self._on_job_executed, EVENT_JOB_EXECUTED)
        self.scheduler.add_listener(self._on_job_error, EVENT_JOB_ERROR)

    # -------------------- Lifecycle --------------------
    def start(self) -> None:
        if not self._started:
            self.scheduler.start()
            self._schedule_housekeeping_jobs()
            self._started = True

    def shutdown(self, wait: bool = True) -> None:
        if self._started:
            self.scheduler.shutdown(wait=wait)
            self._started = False

    # -------------------- Public API --------------------
    def register_task(self, task: Dict[str, Any]) -> None:
        if "id" not in task:
            raise ValueError("Task must include an 'id'")
        # Normalize
        task.setdefault("priority", 3)
        task.setdefault("status", "pending")
        task.setdefault("tags", [])
        task.setdefault("metadata", {})
        self.tasks[task["id"]] = task

    def remove_task(self, task_id: str) -> None:
        self.tasks.pop(task_id, None)

    def schedule_once(self, func, run_at: datetime, job_id: Optional[str] = None, **kwargs) -> None:
        trigger = DateTrigger(run_date=run_at)
        self.scheduler.add_job(func, trigger, id=job_id, kwargs=kwargs, replace_existing=True)

    def schedule_interval(self, func, seconds: int, job_id: Optional[str] = None, **kwargs) -> None:
        trigger = IntervalTrigger(seconds=seconds)
        self.scheduler.add_job(func, trigger, id=job_id, kwargs=kwargs, replace_existing=True)

    def schedule_cron(self, func, cron: str, job_id: Optional[str] = None, **kwargs) -> None:
        """cron like "0 9 * * 1-5" for 9:00 AM Mon-Fri."""
        fields = cron.split()
        if len(fields) != 5:
            raise ValueError("Cron expression must have 5 fields: m h dom mon dow")
        minute, hour, day, month, dow = fields
        trigger = CronTrigger(minute=minute, hour=hour, day=day, month=month, day_of_week=dow)
        self.scheduler.add_job(func, trigger, id=job_id, kwargs=kwargs, replace_existing=True)

    # -------------------- Housekeeping --------------------
    def _schedule_housekeeping_jobs(self) -> None:
        # Deadline checks every 5 minutes
        self.schedule_interval(self._check_deadlines, seconds=300, job_id="housekeeping:deadlines")
        # Priority recalculation every 10 minutes
        self.schedule_interval(self._recalculate_priorities, seconds=600, job_id="housekeeping:priorities")
        # AI suggestions every hour
        self.schedule_interval(self._generate_ai_suggestions, seconds=3600, job_id="housekeeping:ai_suggestions")

    def _check_deadlines(self) -> None:
        now = datetime.utcnow()
        for t in self.tasks.values():
            deadline = t.get("deadline")
            status = t.get("status")
            if not deadline or status == "done":
                continue
            if isinstance(deadline, str):
                try:
                    deadline = datetime.fromisoformat(deadline)
                except Exception:
                    continue
            # Mark overdue
            if deadline < now and status not in {"overdue", "done"}:
                t["status"] = "overdue"
                t.setdefault("metadata", {})
                t["metadata"]["overdue_since"] = now.isoformat()

    def _recalculate_priorities(self) -> None:
        now = datetime.utcnow()
        for t in self.tasks.values():
            if t.get("status") == "done":
                continue
            base = int(t.get("priority", 3))
            deadline = t.get("deadline")
            if isinstance(deadline, str):
                try:
                    deadline = datetime.fromisoformat(deadline)
                except Exception:
                    deadline = None
            urgency_bump = 0
            if deadline:
                delta = (deadline - now).total_seconds()
                if delta <= 0:
                    urgency_bump = -2  # push toward highest urgency
                elif delta < 3600:  # < 1 hour
                    urgency_bump = -1
                elif delta < 24 * 3600:  # < 24 hours
                    urgency_bump = 0
                else:
                    urgency_bump = 1  # can relax priority slightly
            # Keep within 1..5 (1 highest)
            new_priority = max(1, min(5, base + urgency_bump))
            t["priority"] = new_priority

    def _generate_ai_suggestions(self) -> None:
        try:
            pending_tasks = [t for t in self.tasks.values() if t.get("status") != "done"]
            suggestions = self.ai_engine.suggest_next_actions(pending_tasks)
            # Attach suggestions to metadata
            for t in pending_tasks:
                t.setdefault("metadata", {})
                t["metadata"]["ai_suggestions"] = suggestions.get(t.get("id")) if isinstance(suggestions, dict) else suggestions
        except Exception as e:
            # Log or store error for observability; for now, embed in metadata
            for t in self.tasks.values():
                t.setdefault("metadata", {})
                t["metadata"]["ai_suggestions_error"] = str(e)

    # -------------------- Listeners --------------------
    def _on_job_executed(self, event) -> None:
        job = self.scheduler.get_job(event.job_id)
        if not job:
            return
        # basic execution logging in metadata store
        meta = getattr(job, "kwargs", {}) or {}
        meta["last_run_at"] = datetime.utcnow().isoformat()
        meta["result"] = getattr(event, "retval", None)
        job.modify(kwargs=meta)

    def _on_job_error(self, event) -> None:
        job = self.scheduler.get_job(event.job_id)
        if not job:
            return
        meta = getattr(job, "kwargs", {}) or {}
        meta["last_error_at"] = datetime.utcnow().isoformat()
        meta["exception"] = str(getattr(event, "exception", ""))
        job.modify(kwargs=meta)

    # -------------------- Utilities --------------------
    def suggest_schedule_for_task(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Use AI to propose an optimal schedule window and priority for a task."""
        task = self.tasks.get(task_id)
        if not task:
            return None
        try:
            proposal = self.ai_engine.propose_schedule(task)
            return proposal
        except Exception:
            return None

    def schedule_task_by_proposal(self, task_id: str) -> Optional[str]:
        """Use AIEngine proposal to schedule a one-off execution placeholder."""
        proposal = self.suggest_schedule_for_task(task_id)
        if not proposal:
            return None
        run_at: Optional[datetime] = proposal.get("run_at")
        if isinstance(run_at, str):
            try:
                run_at = datetime.fromisoformat(run_at)
            except Exception:
                run_at = None
        if not run_at:
            # fallback: schedule 10 minutes from now
            run_at = datetime.utcnow() + timedelta(minutes=10)

        def noop(task_id: str):
            # Placeholder execution for a scheduled task hook
            t = self.tasks.get(task_id)
            if t:
                t.setdefault("metadata", {})
                t["metadata"]["executed_at"] = datetime.utcnow().isoformat()

        job_id = f"task:{task_id}:once"
        self.schedule_once(noop, run_at, job_id=job_id, task_id=task_id)
        return job_id
