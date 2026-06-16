USE bankdb;

UPDATE Churn_Predictions
SET risk_score = ROUND(risk_score * 100, 2)
WHERE risk_score < 1.01;
