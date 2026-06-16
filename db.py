from decimal import Decimal
from datetime import date, datetime

from sqlalchemy import create_engine, text
import pandas as pd
import os

from db_config import get_database_url

DB_URL = get_database_url()
engine = create_engine(DB_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)


def _row_dict(row) -> dict:
    """Make SQL rows JSON-safe for FastAPI (Decimal → float, dates → str)."""
    if row is None:
        return {}
    d = dict(row._mapping)
    out = {}
    for k, v in d.items():
        if isinstance(v, Decimal):
            out[k] = float(v)
        elif isinstance(v, datetime):
            out[k] = v.isoformat(sep=" ", timespec="seconds")
        elif isinstance(v, date):
            out[k] = v.isoformat()
        else:
            out[k] = v
    return out


def ensure_ml_schema() -> None:
    """
    Create Churn_Alerts + vw_model_features if missing (normally from db_setup.sql).
    Safe to call every startup.
    """
    churn_ddl = text("""
        CREATE TABLE IF NOT EXISTS Churn_Alerts (
            alert_id      INT AUTO_INCREMENT PRIMARY KEY,
            customer_id   INT NOT NULL,
            risk_score    DECIMAL(5,2),
            risk_band     ENUM('High','Medium','Low'),
            alert_message TEXT,
            alert_sent    TINYINT(1) DEFAULT 0,
            created_at    DATETIME DEFAULT CURRENT_TIMESTAMP,
            actioned_at   DATETIME NULL,
            UNIQUE KEY uq_customer (customer_id),
            FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
        )
    """)
    view_ddl = text("""
        CREATE OR REPLACE VIEW vw_model_features AS
        SELECT
            c.customer_id,
            c.credit_score,
            c.country,
            c.gender,
            c.age,
            c.tenure,
            COALESCE(SUM(a.balance), 0) AS balance,
            c.prd_number AS products_number,
            IF(cc.customer_id IS NOT NULL, 1, 0) AS credit_card,
            IF(bs.login_frequency > 0 AND bs.txn_count_30d > 0, 1, 0) AS active_member,
            c.salary AS estimated_salary
        FROM Customer c
        LEFT JOIN Account_Holders h ON c.customer_id = h.customer_id AND h.role = 'primary'
        LEFT JOIN Account a ON h.account_id = a.account_id AND a.status = 'active'
        LEFT JOIN Credit_Card cc ON c.customer_id = cc.customer_id AND cc.status = 'active'
        LEFT JOIN Behavior_Summary bs ON c.customer_id = bs.customer_id
        GROUP BY c.customer_id
    """)

    with engine.begin() as conn:
        conn.execute(churn_ddl)
        conn.execute(view_ddl)
        # normalize_scores removed as it corrupts valid <1.01% scores


def fetch_features(customer_ids: list[int] | None = None) -> pd.DataFrame:
    """Pull the 10 model features from vw_model_features. Optionally filter by IDs."""
    query = "SELECT * FROM vw_model_features"
    if customer_ids:
        ids = ",".join(str(i) for i in customer_ids)
        query += f" WHERE customer_id IN ({ids})"
    with engine.connect() as conn:
        return pd.read_sql(text(query), conn)


def write_predictions(df: pd.DataFrame):
    """Upsert risk_score (0–100) into Churn_Predictions."""
    rows = df[["customer_id", "risk_score"]].to_dict(orient="records")
    upsert_sql = text("""
        INSERT INTO Churn_Predictions (customer_id, risk_score, last_updated)
        VALUES (:customer_id, :risk_score, NOW())
        ON DUPLICATE KEY UPDATE
            risk_score   = VALUES(risk_score),
            last_updated = NOW()
    """)
    with engine.begin() as conn:
        conn.execute(upsert_sql, rows)


def get_dashboard_stats() -> dict:
    sql = text("""
        SELECT
            COUNT(*) AS total_customers,
            SUM(CASE WHEN cp.risk_score >= 75 THEN 1 ELSE 0 END) AS high_risk,
            SUM(CASE WHEN cp.risk_score >= 40 AND cp.risk_score < 75 THEN 1 ELSE 0 END) AS medium_risk,
            SUM(CASE WHEN cp.risk_score < 40 THEN 1 ELSE 0 END) AS low_risk,
            ROUND(AVG(cp.risk_score), 2) AS avg_risk_score
        FROM Customer c
        LEFT JOIN Churn_Predictions cp ON c.customer_id = cp.customer_id
    """)
    with engine.connect() as conn:
        row = conn.execute(sql).fetchone()
        return _row_dict(row) if row else {}


def get_all_customers(limit: int = 100, offset: int = 0, risk_band: str | None = None) -> list[dict]:
    where = ""
    if risk_band == "High":
        where = "WHERE cp.risk_score >= 75"
    elif risk_band == "Medium":
        where = "WHERE cp.risk_score >= 40 AND cp.risk_score < 75"
    elif risk_band == "Low":
        where = "WHERE cp.risk_score < 40 OR cp.risk_score IS NULL"

    sql = text(f"""
        SELECT
            c.customer_id, c.name, c.age, c.gender, c.country,
            c.credit_score, c.tenure, c.salary AS estimated_salary, c.prd_number AS products_number,
            COALESCE(SUM(a.balance), 0) AS balance,
            MAX(IF(cc.customer_id IS NOT NULL, 1, 0)) AS credit_card,
            MAX(IF(bs.login_frequency > 0 AND bs.txn_count_30d > 0, 1, 0)) AS active_member,
            MAX(bs.txn_count_30d) AS txn_count_30d,
            MAX(bs.avg_balance) AS avg_balance,
            MAX(bs.complaint_count) AS complaint_count,
            MAX(bs.login_frequency) AS login_frequency,
            COALESCE(MAX(cp.risk_score), 0) AS risk_score,
            CASE
                WHEN MAX(cp.risk_score) >= 75 THEN 'High'
                WHEN MAX(cp.risk_score) >= 40 THEN 'Medium'
                ELSE 'Low'
            END AS risk_band,
            MAX(cp.last_updated) AS score_updated_at
        FROM Customer c
        LEFT JOIN Account_Holders h ON c.customer_id = h.customer_id AND h.role = 'primary'
        LEFT JOIN Account a ON h.account_id = a.account_id AND a.status = 'active'
        LEFT JOIN Credit_Card cc ON c.customer_id = cc.customer_id AND cc.status = 'active'
        LEFT JOIN Behavior_Summary bs ON c.customer_id = bs.customer_id
        LEFT JOIN Churn_Predictions cp ON c.customer_id = cp.customer_id
        {where}
        GROUP BY c.customer_id, c.name, c.age, c.gender, c.country,
                 c.credit_score, c.tenure, c.salary, c.prd_number
        ORDER BY COALESCE(MAX(cp.risk_score), 0) DESC
        LIMIT :limit OFFSET :offset
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit, "offset": offset}).fetchall()
        return [_row_dict(r) for r in rows]


def get_customer_detail(customer_id: int) -> dict | None:
    sql = text("""
        SELECT
            c.customer_id, c.name, c.age, c.gender, c.country, c.credit_score,
            c.tenure, c.salary AS estimated_salary, c.prd_number AS products_number,
            COALESCE(SUM(a.balance), 0) AS balance,
            MAX(IF(cc.customer_id IS NOT NULL, 1, 0)) AS credit_card,
            MAX(IF(bs.login_frequency > 0 AND bs.txn_count_30d > 0, 1, 0)) AS active_member,
            MAX(bs.txn_count_30d) AS txn_count_30d,
            MAX(bs.avg_balance) AS avg_balance,
            MAX(bs.complaint_count) AS complaint_count,
            MAX(bs.login_frequency) AS login_frequency,
            MAX(cc.credit_limit) AS credit_limit,
            MAX(cc.outstanding_balance) AS card_outstanding,
            MAX(cc.card_type) AS card_type,
            COALESCE(MAX(al.outstanding), 0) AS outstanding_loans,
            COALESCE(MAX(al.total_loans), 0) AS total_loans,
            COALESCE(MAX(cp.risk_score), 0) AS risk_score,
            MAX(cp.last_updated) AS score_updated_at,
            CASE WHEN MAX(cp.risk_score) >= 75 THEN 'High'
                 WHEN MAX(cp.risk_score) >= 40 THEN 'Medium'
                 ELSE 'Low' END AS risk_band
        FROM Customer c
        LEFT JOIN Account_Holders h ON c.customer_id = h.customer_id AND h.role = 'primary'
        LEFT JOIN Account a ON h.account_id = a.account_id AND a.status = 'active'
        LEFT JOIN Credit_Card cc ON c.customer_id = cc.customer_id AND cc.status = 'active'
        LEFT JOIN Behavior_Summary bs ON c.customer_id = bs.customer_id
        LEFT JOIN (
            SELECT l.customer_id,
                   COUNT(*) AS total_loans,
                   SUM(l.amount) - COALESCE(SUM(lp_agg.paid), 0) AS outstanding
            FROM Loan l
            LEFT JOIN (SELECT loan_id, SUM(amount) AS paid FROM Loan_Payments GROUP BY loan_id) lp_agg
              ON l.loan_id = lp_agg.loan_id
            WHERE l.status = 'active'
            GROUP BY l.customer_id
        ) al ON c.customer_id = al.customer_id
        LEFT JOIN Churn_Predictions cp ON c.customer_id = cp.customer_id
        WHERE c.customer_id = :cid
        GROUP BY c.customer_id, c.name, c.age, c.gender, c.country, c.credit_score,
                 c.tenure, c.salary, c.prd_number
    """)
    with engine.connect() as conn:
        row = conn.execute(sql, {"cid": customer_id}).fetchone()
        return _row_dict(row) if row else None


def get_unactioned_alerts(limit: int = 20) -> list[dict]:
    sql = text("""
        SELECT ca.alert_id, ca.customer_id, c.name, c.country, c.age,
               ca.risk_score, ca.risk_band, ca.alert_message, ca.created_at
        FROM Churn_Alerts ca
        JOIN Customer c ON ca.customer_id = c.customer_id
        WHERE ca.alert_sent = 0
        ORDER BY ca.risk_score DESC
        LIMIT :limit
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql, {"limit": limit}).fetchall()
        return [_row_dict(r) for r in rows]


def mark_alert_actioned(customer_id: int):
    sql = text("""
        UPDATE Churn_Alerts SET alert_sent = 1, actioned_at = NOW()
        WHERE customer_id = :cid AND alert_sent = 0
    """)
    with engine.begin() as conn:
        conn.execute(sql, {"cid": customer_id})


def get_risk_distribution() -> list[dict]:
    sql = text("""
        SELECT
            CASE WHEN cp.risk_score >= 75 THEN 'High'
                 WHEN cp.risk_score >= 40 THEN 'Medium'
                 ELSE 'Low' END AS risk_band,
            COUNT(*) AS count
        FROM Churn_Predictions cp
        GROUP BY
            CASE WHEN cp.risk_score >= 75 THEN 'High'
                 WHEN cp.risk_score >= 40 THEN 'Medium'
                 ELSE 'Low' END
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()
        return [_row_dict(r) for r in rows]


def get_country_risk() -> list[dict]:
    sql = text("""
        SELECT c.country, ROUND(AVG(cp.risk_score), 2) AS avg_risk, COUNT(*) AS customer_count
        FROM Customer c
        JOIN Churn_Predictions cp ON c.customer_id = cp.customer_id
        GROUP BY c.country ORDER BY avg_risk DESC
    """)
    with engine.connect() as conn:
        rows = conn.execute(sql).fetchall()
        return [_row_dict(r) for r in rows]


def create_customer(data: dict) -> int:
    sql = text("""
        INSERT INTO Customer
            (name, age, gender, country, salary, tenure, prd_number, credit_score, created_at)
        VALUES
            (:name, :age, :gender, :country, :salary, :tenure, :prd_number, :credit_score,
             COALESCE(:created_at, CURDATE()))
    """)
    with engine.begin() as conn:
        result = conn.execute(sql, data)
        new_id = result.lastrowid

    seed_sql = text("""
        INSERT IGNORE INTO Behavior_Summary
            (customer_id, txn_count_30d, avg_balance, balance_drop_rate, complaint_count, login_frequency, churn_label)
        VALUES (:cid, 0, 0, 0, 0, 0, 0)
    """)
    with engine.begin() as conn:
        conn.execute(seed_sql, {"cid": new_id})

    return new_id


def update_customer(customer_id: int, data: dict) -> bool:
    allowed = {
        "name", "age", "gender", "country",
        "salary", "tenure", "prd_number", "credit_score"
    }
    fields = {k: v for k, v in data.items() if k in allowed and v is not None}
    if not fields:
        return False

    set_clause = ", ".join(f"{col} = :{col}" for col in fields)
    sql = text(f"UPDATE Customer SET {set_clause} WHERE customer_id = :customer_id")
    fields["customer_id"] = customer_id

    with engine.begin() as conn:
        result = conn.execute(sql, fields)
        return result.rowcount > 0


def delete_customer(customer_id: int) -> bool:
    delete_steps = [
        "DELETE FROM Churn_Alerts      WHERE customer_id = :cid",
        "DELETE FROM Churn_Predictions WHERE customer_id = :cid",
        "DELETE FROM Behavior_Summary  WHERE customer_id = :cid",
        "DELETE FROM Login_Activity    WHERE customer_id = :cid",
        "DELETE FROM Support_Tickets   WHERE customer_id = :cid",
        "DELETE FROM Beneficiary       WHERE customer_id = :cid",
        """DELETE lp FROM Loan_Payments lp
           JOIN Loan l ON lp.loan_id = l.loan_id
           WHERE l.customer_id = :cid""",
        "DELETE FROM Loan WHERE customer_id = :cid",
        "DELETE FROM Credit_Card WHERE customer_id = :cid",
        """DELETE t FROM Transactions t
           JOIN Account_Holders h ON t.account_id = h.account_id
           WHERE h.customer_id = :cid""",
        "DELETE FROM Account_Holders WHERE customer_id = :cid",
        """DELETE a FROM Account a
           WHERE NOT EXISTS (
               SELECT 1 FROM Account_Holders ah WHERE ah.account_id = a.account_id
           )""",
        "DELETE FROM Customer WHERE customer_id = :cid",
    ]

    with engine.begin() as conn:
        for stmt in delete_steps:
            conn.execute(text(stmt), {"cid": customer_id})
        check = conn.execute(
            text("SELECT COUNT(*) FROM Customer WHERE customer_id = :cid"),
            {"cid": customer_id}
        ).scalar()
        return check == 0


def customer_exists(customer_id: int) -> bool:
    with engine.connect() as conn:
        n = conn.execute(
            text("SELECT COUNT(*) FROM Customer WHERE customer_id = :cid"),
            {"cid": customer_id}
        ).scalar()
        return n > 0
