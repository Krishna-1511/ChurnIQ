USE bankdb;

CREATE OR REPLACE VIEW vw_model_features AS
SELECT
    c.customer_id,
    c.credit_score,
    c.country,
    c.gender,
    c.age,
    c.tenure,
    COALESCE(SUM(a.balance), 0)                                      AS balance,
    c.prd_number                                                      AS products_number,
    IF(cc.customer_id IS NOT NULL, 1, 0)                              AS credit_card,
    IF(bs.login_frequency > 0 AND bs.txn_count_30d > 0, 1, 0)        AS active_member,
    c.salary                                                          AS estimated_salary
FROM Customer c
LEFT JOIN Account_Holders h   ON c.customer_id = h.customer_id AND h.role = 'primary'
LEFT JOIN Account a           ON h.account_id = a.account_id AND a.status = 'active'
LEFT JOIN Credit_Card cc      ON c.customer_id = cc.customer_id AND cc.status = 'active'
LEFT JOIN Behavior_Summary bs ON c.customer_id = bs.customer_id
GROUP BY c.customer_id;

CREATE TABLE IF NOT EXISTS Churn_Alerts (
    alert_id      INT AUTO_INCREMENT PRIMARY KEY,
    customer_id   INT NOT NULL,
    risk_score    DECIMAL(5,2),
    risk_band     ENUM('High','Medium','Low'),
    alert_message TEXT,
    alert_sent    TINYINT(1) DEFAULT 0,
    created_at    DATETIME DEFAULT NOW(),
    actioned_at   DATETIME NULL,
    UNIQUE KEY uq_customer (customer_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

DELIMITER $$

DROP TRIGGER IF EXISTS trg_churn_alert$$
CREATE TRIGGER trg_churn_alert
AFTER INSERT ON Churn_Predictions
FOR EACH ROW
BEGIN
    DECLARE v_name    VARCHAR(100);
    DECLARE v_country VARCHAR(50);
    DECLARE v_band    VARCHAR(10);
    DECLARE v_msg     TEXT;

    SELECT name, country INTO v_name, v_country
    FROM Customer WHERE customer_id = NEW.customer_id;

    SET v_band = CASE
        WHEN NEW.risk_score >= 75 THEN 'High'
        WHEN NEW.risk_score >= 40 THEN 'Medium'
        ELSE 'Low'
    END;

    IF NEW.risk_score >= 40 THEN
        SET v_msg = CONCAT(
            'Customer ', v_name, ' (ID: ', NEW.customer_id, ') from ',
            v_country, ' has a churn risk score of ', NEW.risk_score, '% — classified as ', v_band, ' risk.'
        );
        INSERT INTO Churn_Alerts (customer_id, risk_score, risk_band, alert_message, alert_sent, created_at)
        VALUES (NEW.customer_id, NEW.risk_score, v_band, v_msg, 0, NOW())
        ON DUPLICATE KEY UPDATE
            risk_score    = NEW.risk_score,
            risk_band     = v_band,
            alert_message = v_msg,
            alert_sent    = 0,
            created_at    = NOW();
    END IF;
END$$

DROP TRIGGER IF EXISTS trg_churn_alert_update$$
CREATE TRIGGER trg_churn_alert_update
AFTER UPDATE ON Churn_Predictions
FOR EACH ROW
BEGIN
    DECLARE v_name    VARCHAR(100);
    DECLARE v_country VARCHAR(50);
    DECLARE v_band    VARCHAR(10);
    DECLARE v_msg     TEXT;

    IF OLD.risk_score <> NEW.risk_score THEN
        SELECT name, country INTO v_name, v_country
        FROM Customer WHERE customer_id = NEW.customer_id;

        SET v_band = CASE
            WHEN NEW.risk_score >= 75 THEN 'High'
            WHEN NEW.risk_score >= 40 THEN 'Medium'
            ELSE 'Low'
        END;

        IF NEW.risk_score >= 40 THEN
            SET v_msg = CONCAT(
                'Score updated for ', v_name, ' (ID: ', NEW.customer_id, '): ',
                OLD.risk_score, '% → ', NEW.risk_score, '% (', v_band, ')'
            );
            INSERT INTO Churn_Alerts (customer_id, risk_score, risk_band, alert_message, alert_sent, created_at)
            VALUES (NEW.customer_id, NEW.risk_score, v_band, v_msg, 0, NOW())
            ON DUPLICATE KEY UPDATE
                risk_score    = NEW.risk_score,
                risk_band     = v_band,
                alert_message = v_msg,
                alert_sent    = 0,
                created_at    = NOW();
        ELSE
            DELETE FROM Churn_Alerts WHERE customer_id = NEW.customer_id AND alert_sent = 0;
        END IF;
    END IF;
END$$

DELIMITER ;
