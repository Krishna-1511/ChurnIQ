"""
scheduler.py — Run as a standalone process alongside the FastAPI server.
    python scheduler.py

Schedules:
  - Nightly 2am  : full batch re-score of all customers
  - Every hour   : targeted re-score for customers who logged in the past hour
"""
import logging
from apscheduler.schedulers.blocking import BlockingScheduler
from sqlalchemy import text
from db import engine
from ml_pipeline import run_pipeline

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
log = logging.getLogger(__name__)

scheduler = BlockingScheduler(timezone="Asia/Kolkata")


@scheduler.scheduled_job("cron", hour=2, minute=0, id="nightly_batch")
def nightly_batch():
    log.info("Nightly batch scoring started")
    result = run_pipeline()
    log.info(f"Nightly batch complete: {result}")


@scheduler.scheduled_job("cron", minute=0, id="hourly_incremental")
def hourly_incremental():
    log.info("Hourly incremental scoring started")
    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT DISTINCT customer_id FROM Login_Activity
            WHERE login_time >= DATE_SUB(NOW(), INTERVAL 1 HOUR)
        """)).fetchall()
        ids = [r[0] for r in rows]

    if ids:
        log.info(f"Re-scoring {len(ids)} recently active customers")
        result = run_pipeline(customer_ids=ids)
        log.info(f"Incremental done: {result}")
    else:
        log.info("No recent logins — skipping incremental score")


if __name__ == "__main__":
    log.info("Scheduler starting… (Ctrl-C to stop)")
    scheduler.start()
