import random
from datetime import datetime, timedelta

random.seed(42)

def d2(x):
    return f"{float(x):.2f}"

def esc(s):
    return s.replace("\\", "\\\\").replace("'", "''")

# Customers 31-60
names = [
    ("Rajesh Kumar", "male", "India"), ("Priya Sharma", "female", "India"), ("Amit Patel", "male", "India"),
    ("Sneha Reddy", "female", "India"), ("Vikram Singh", "male", "India"), ("Ananya Iyer", "female", "India"),
    ("Rohit Mehta", "male", "India"), ("Kavita Nair", "female", "India"), ("Suresh Joshi", "male", "India"),
    ("Deepika Rao", "female", "India"), ("James Mitchell", "male", "USA"), ("Emily Carter", "female", "USA"),
    ("Michael Brooks", "male", "USA"), ("Sarah Johnson", "female", "USA"), ("David Nguyen", "male", "USA"),
    ("Jessica Williams", "female", "USA"), ("Brian Anderson", "male", "USA"), ("Amanda Lee", "female", "USA"),
    ("Christopher Davis", "male", "USA"), ("Nicole Martinez", "female", "USA"), ("Oliver Thompson", "male", "UK"),
    ("Charlotte Evans", "female", "UK"), ("Harry Wilson", "male", "UK"), ("Sophie Clarke", "female", "UK"),
    ("George Hughes", "male", "UK"), ("Emma Davies", "female", "UK"), ("Jack Morgan", "male", "UK"),
    ("Isla Roberts", "female", "UK"), ("Thomas Green", "male", "UK"), ("Lucy Baker", "female", "UK"),
]

lines = []

# Customer
vals = []
for i, (name, gender, country) in enumerate(names, start=31):
    age = random.randint(22, 55)
    salary = random.randint(30000, 150000)
    tenure = random.randint(1, 10)
    prd = random.randint(1, 5)
    cs = random.randint(580, 800)
    start = datetime(2018, 1, 1)
    end = datetime(2024, 6, 1)
    delta = (end - start).days
    created = start + timedelta(days=random.randint(0, delta))
    vals.append(f"({i}, '{esc(name)}', {age}, '{gender}', '{country}', {d2(salary)}, {tenure}, {prd}, {cs}, '{created.date()}')")
lines.append("INSERT INTO Customer (customer_id, name, age, gender, country, salary, tenure, prd_number, credit_score, created_at) VALUES\n" + ",\n".join(vals) + ";")

# Account 131-160: customer i maps to account 100+i
acc_vals = []
for aid in range(131, 161):
    bid = random.choice([1, 2])
    atype = random.choice(["savings", "current"])
    bal = random.randint(5000, 150000) + random.random()
    status = "active" if random.random() < 0.9 else "closed"
    start = datetime(2019, 1, 1)
    end = datetime(2024, 1, 1)
    delta = (end - start).days
    created = start + timedelta(days=random.randint(0, max(0, delta)))
    acc_vals.append(f"({aid}, {bid}, '{atype}', {d2(bal)}, '{status}', '{created.date()}')")
lines.append("INSERT INTO Account (account_id, branch_id, account_type, balance, status, created_at) VALUES\n" + ",\n".join(acc_vals) + ";")

# Account_Holders: primary customer_id = account_id - 100 for 131->31
ah_vals = []
secondary_accounts = {131, 138, 145, 152, 159}  # 5 accounts with secondary
for aid in range(131, 161):
    cid = aid - 100
    ah_vals.append(f"({aid}, {cid}, 'primary')")
    if aid in secondary_accounts:
        sec = cid + 1 if cid < 60 else cid - 1
        if sec == cid:
            sec = 32
        ah_vals.append(f"({aid}, {sec}, 'secondary')")
lines.append("INSERT INTO Account_Holders (account_id, customer_id, role) VALUES\n" + ",\n".join(ah_vals) + ";")

# Credit_Card 31-60: account_id = customer_id + 100
cc_vals = []
for cid in range(31, 61):
    aid = cid + 100
    ctype = random.choice(["visa", "mastercard", "rupay"])
    limit = random.randint(20000, 200000) + random.random()
    out = random.uniform(0, float(limit) * 0.85)
    status = "active" if random.random() < 0.92 else "blocked"
    ey = random.randint(2026, 2030)
    em = random.randint(1, 12)
    ed = random.randint(1, 28)
    exp = f"{ey:04d}-{em:02d}-{ed:02d}"
    cc_vals.append(f"({cid}, {cid}, {aid}, '{ctype}', {d2(limit)}, {d2(out)}, '{status}', '{exp}')")
lines.append("INSERT INTO Credit_Card (card_id, customer_id, account_id, card_type, credit_limit, outstanding_balance, status, expiry_date) VALUES\n" + ",\n".join(cc_vals) + ";")

# Transactions: 10-15 per account 131-160, no txn_id
all_accounts = list(range(101, 161))
txn_rows = []
for aid in range(131, 161):
    n = random.randint(10, 15)
    for _ in range(n):
        ttype = random.choices(["credit", "debit", "transfer"], weights=[0.35, 0.45, 0.20])[0]
        amt = random.randint(500, 50000) + round(random.random(), 2)
        start = datetime(2024, 1, 1)
        end = datetime(2024, 12, 31, 23, 59, 59)
        ts = start + timedelta(seconds=random.randint(0, int((end - start).total_seconds())))
        status = "success" if random.random() < 0.9 else "failed"
        ref = "NULL"
        if ttype == "transfer":
            others = [x for x in all_accounts if x != aid]
            ref = str(random.choice(others))
        txn_rows.append(f"({aid}, '{ttype}', {d2(amt)}, '{ts.strftime('%Y-%m-%d %H:%M:%S')}', '{status}', {ref})")
lines.append("INSERT INTO Transactions (account_id, txn_type, amount, txn_date, status, reference_account) VALUES\n" + ",\n".join(txn_rows) + ";")

# Loan 31-60
loan_types = ["home", "car", "personal", "education"]
loan_vals = []
for lid in range(31, 61):
    cid = lid
    lt = random.choice(loan_types)
    amt = random.randint(50000, 800000) + random.random()
    ir = round(random.uniform(6.0, 12.0), 2)
    st = random.choice(["active", "closed"])
    loan_vals.append(f"({lid}, {cid}, '{lt}', {d2(amt)}, {d2(ir)}, '{st}')")
lines.append("INSERT INTO Loan (loan_id, customer_id, loan_type, amount, interest_rate, status) VALUES\n" + ",\n".join(loan_vals) + ";")

# Loan_Payments one per loan 31-60
pay_vals = []
for lid in range(31, 61):
    pamt = random.randint(3000, 15000) + random.random()
    start = datetime(2024, 2, 1)
    end = datetime(2024, 12, 1)
    pd = start + timedelta(days=random.randint(0, (end - start).days))
    pay_vals.append(f"({lid}, {d2(pamt)}, '{pd.date()}')")
lines.append("INSERT INTO Loan_Payments (loan_id, amount, payment_date) VALUES\n" + ",\n".join(pay_vals) + ";")

# Support tickets 1-2 per customer 31-60
issues = ["Card Issue", "Login Issue", "Fraud Alert", "Transfer Delay", "Loan Query", "App Crash", "Balance Issue"]
ticket_rows = []
for cid in range(31, 61):
    for _ in range(random.randint(1, 2)):
        it = random.choice(issues)
        desc = esc(f"Customer reported: {it.lower()} requiring follow-up.")
        sent = random.choice(["positive", "neutral", "negative"])
        st = random.choice(["open", "closed"])
        cstart = datetime(2024, 1, 1)
        cend = datetime(2024, 12, 31)
        created = cstart + timedelta(seconds=random.randint(0, int((cend - cstart).total_seconds())))
        if st == "closed":
            resolved = created + timedelta(days=random.randint(1, 3))
            res_s = f"'{resolved.strftime('%Y-%m-%d %H:%M:%S')}'"
        else:
            res_s = "NULL"
        ticket_rows.append(f"({cid}, '{it}', '{desc}', '{sent}', '{st}', '{created.strftime('%Y-%m-%d %H:%M:%S')}', {res_s})")
lines.append("INSERT INTO Support_Tickets (customer_id, issue_type, description, sentiment, status, created_at, resolved_at) VALUES\n" + ",\n".join(ticket_rows) + ";")

# Login_Activity 2-4 per customer
login_rows = []
for cid in range(31, 61):
    for _ in range(random.randint(2, 4)):
        d0 = datetime(2024, 1, 1)
        d1 = datetime(2024, 12, 31)
        day = d0 + timedelta(days=random.randint(0, (d1 - d0).days))
        h = random.randint(7, 22)
        m = random.randint(0, 59)
        s = random.randint(0, 59)
        lt = day.replace(hour=h, minute=m, second=s)
        login_rows.append(f"({cid}, '{lt.strftime('%Y-%m-%d %H:%M:%S')}')")
lines.append("INSERT INTO Login_Activity (customer_id, login_time) VALUES\n" + ",\n".join(login_rows) + ";")

# Beneficiary 6-15: 10 rows, customer 31-60, beneficiary_account in 101-160 not own
own_account = {c: c + 100 for c in range(31, 61)}
ben_rows = []
for bid in range(6, 16):
    cid = random.randint(31, 60)
    own = own_account[cid]
    choices = [a for a in range(101, 161) if a != own]
    bacc = random.choice(choices)
    ben_rows.append(f"({bid}, {cid}, {bacc})")
lines.append("INSERT INTO Beneficiary (beneficiary_id, customer_id, beneficiary_account) VALUES\n" + ",\n".join(ben_rows) + ";")

# Behavior_Summary
bs_vals = []
for cid in range(31, 61):
    tc = random.randint(5, 20)
    ab = random.randint(5000, 120000) + random.random()
    bdr = round(random.uniform(0.0, 0.50), 2)
    cc = random.randint(0, 5)
    lf = random.randint(1, 30)
    cl = random.choice([0, 1])
    bs_vals.append(f"({cid}, {tc}, {d2(ab)}, {d2(bdr)}, {cc}, {lf}, {cl})")
lines.append("INSERT INTO Behavior_Summary (customer_id, txn_count_30d, avg_balance, balance_drop_rate, complaint_count, login_frequency, churn_label) VALUES\n" + ",\n".join(bs_vals) + ";")

# Churn_Predictions
cp_vals = []
for cid in range(31, 61):
    rs = round(random.uniform(0.05, 0.95), 2)
    y0 = datetime(2024, 1, 1)
    y1 = datetime(2024, 12, 31, 23, 59, 59)
    lu = y0 + timedelta(seconds=random.randint(0, int((y1 - y0).total_seconds())))
    cp_vals.append(f"({cid}, {d2(rs)}, '{lu.strftime('%Y-%m-%d %H:%M:%S')}')")
lines.append("INSERT INTO Churn_Predictions (customer_id, risk_score, last_updated) VALUES\n" + ",\n".join(cp_vals) + ";")

with open("seed_extension.sql", "w", encoding="utf-8", newline="\n") as f:
    f.write("\n\n".join(lines))
    f.write("\n")

print("Written seed_extension.sql")
print("Transactions:", len(txn_rows))
