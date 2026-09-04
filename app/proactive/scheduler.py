"""
Proactive Scheduler — APScheduler background jobs integrated with FastAPI lifespan.

The scheduler runs a periodic check for each active user and calls the
proactive decision engine. If decision=INITIATE, message_planner generates
the message and it is stored (ready for the notification layer to deliver).

This module exposes:
  start_scheduler()  — call from FastAPI startup (app/api/main.py lifespan)
  stop_scheduler()   — call from FastAPI shutdown

Scheduling interval: every 30 minutes (configurable).
"""
from __future__ import annotations

import logging

logger = logging.getLogger(__name__)

_scheduler = None
CHECK_INTERVAL_MINUTES = 30


def _proactive_check_job() -> None:
    """
    Periodic job: check all active users for proactive opportunities.
    In MVP, this is a stub that logs — full integration with decision_engine
    and notification layer happens after the DB and user management are complete.
    """
    logger.debug("Proactive check job running.")
    # TODO (post-MVP): iterate active users, call decision_engine.evaluate(),
    # call message_planner.plan(), store result for notification delivery.


def start_scheduler() -> None:
    """Start the APScheduler background scheduler."""
    global _scheduler
    try:
        from apscheduler.schedulers.background import BackgroundScheduler

        _scheduler = BackgroundScheduler()
        _scheduler.add_job(
            _proactive_check_job,
            trigger="interval",
            minutes=CHECK_INTERVAL_MINUTES,
            id="proactive_check",
            replace_existing=True,
        )
        _scheduler.start()
        logger.info("Proactive scheduler started (interval: %dm).", CHECK_INTERVAL_MINUTES)
    except ImportError:
        logger.warning(
            "APScheduler not installed — proactive scheduler disabled. "
            "Install apscheduler to enable background proactive messages."
        )
    except Exception as exc:
        logger.error("Proactive scheduler failed to start: %s", exc)


def stop_scheduler() -> None:
    """Shut down the scheduler gracefully."""
    global _scheduler
    if _scheduler and _scheduler.running:
        _scheduler.shutdown(wait=False)
        logger.info("Proactive scheduler stopped.")
    _scheduler = None
