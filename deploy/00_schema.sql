USE bankdb;

SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

DROP TABLE IF EXISTS Churn_Alerts;
DROP TABLE IF EXISTS Churn_Predictions;
DROP TABLE IF EXISTS Behavior_Summary;
DROP TABLE IF EXISTS Beneficiary;
DROP TABLE IF EXISTS Login_Activity;
DROP TABLE IF EXISTS Loan_Payments;
DROP TABLE IF EXISTS Loan;
DROP TABLE IF EXISTS Support_Tickets;
DROP TABLE IF EXISTS Transactions;
DROP TABLE IF EXISTS Credit_Card;
DROP TABLE IF EXISTS Account_Holders;
DROP TABLE IF EXISTS Account;
DROP TABLE IF EXISTS Customer;
DROP TABLE IF EXISTS Branch;
DROP TABLE IF EXISTS Bank;

SET FOREIGN_KEY_CHECKS = 1;

CREATE TABLE Customer (
    customer_id INT PRIMARY KEY,
    name VARCHAR(100),
    age INT,
    gender ENUM('male','female','other'),
    country VARCHAR(50),
    salary DECIMAL(12,2),
    tenure INT,
    prd_number INT,
    credit_score INT,
    created_at DATE
);

CREATE TABLE Bank (
    bank_id INT PRIMARY KEY,
    name VARCHAR(100),
    code VARCHAR(20),
    address VARCHAR(200)
);

CREATE TABLE Branch (
    branch_id INT PRIMARY KEY,
    bank_id INT,
    name VARCHAR(100),
    address VARCHAR(200),
    FOREIGN KEY (bank_id) REFERENCES Bank(bank_id)
);

CREATE TABLE Account (
    account_id INT PRIMARY KEY,
    branch_id INT,
    account_type ENUM('savings','current'),
    balance DECIMAL(12,2),
    status ENUM('active','closed'),
    created_at DATE,
    FOREIGN KEY (branch_id) REFERENCES Branch(branch_id)
);

CREATE TABLE Account_Holders (
    account_id INT,
    customer_id INT,
    role ENUM('primary','secondary'),
    PRIMARY KEY (account_id, customer_id),
    FOREIGN KEY (account_id) REFERENCES Account(account_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE Transactions (
    txn_id INT AUTO_INCREMENT PRIMARY KEY,
    account_id INT,
    txn_type ENUM('credit','debit','transfer'),
    amount DECIMAL(12,2),
    txn_date DATETIME,
    status ENUM('success','failed'),
    reference_account INT NULL,
    FOREIGN KEY (account_id) REFERENCES Account(account_id)
);

CREATE TABLE Support_Tickets (
    ticket_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    issue_type VARCHAR(100),
    description TEXT,
    sentiment ENUM('positive','neutral','negative'),
    status ENUM('open','closed'),
    created_at DATETIME,
    resolved_at DATETIME NULL,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE Loan (
    loan_id INT PRIMARY KEY,
    customer_id INT,
    loan_type VARCHAR(50),
    amount DECIMAL(12,2),
    interest_rate DECIMAL(5,2),
    status ENUM('active','closed'),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE Loan_Payments (
    payment_id INT AUTO_INCREMENT PRIMARY KEY,
    loan_id INT,
    amount DECIMAL(12,2),
    payment_date DATE,
    FOREIGN KEY (loan_id) REFERENCES Loan(loan_id)
);

CREATE TABLE Credit_Card (
    card_id INT PRIMARY KEY,
    customer_id INT,
    account_id INT,
    card_type ENUM('visa','mastercard','rupay'),
    credit_limit DECIMAL(12,2),
    outstanding_balance DECIMAL(12,2),
    status ENUM('active','blocked'),
    expiry_date DATE,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id),
    FOREIGN KEY (account_id) REFERENCES Account(account_id)
);

CREATE TABLE Login_Activity (
    login_id INT AUTO_INCREMENT PRIMARY KEY,
    customer_id INT,
    login_time DATETIME,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE Beneficiary (
    beneficiary_id INT PRIMARY KEY,
    customer_id INT,
    beneficiary_account INT,
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE Behavior_Summary (
    customer_id INT,
    txn_count_30d INT,
    avg_balance DECIMAL(12,2),
    balance_drop_rate DECIMAL(5,2),
    complaint_count INT,
    login_frequency INT,
    churn_label INT,
    PRIMARY KEY (customer_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);

CREATE TABLE Churn_Predictions (
    customer_id INT,
    risk_score DECIMAL(5,2),
    last_updated DATETIME,
    PRIMARY KEY (customer_id),
    FOREIGN KEY (customer_id) REFERENCES Customer(customer_id)
);
