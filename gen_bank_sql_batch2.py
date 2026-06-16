import random
from datetime import datetime, timedelta

random.seed(987654321)

def d2(x):
    return f"{float(x):.2f}"

def esc(s):
    return s.replace("\\", "\\\\").replace("'", "''")

CUST_START, CUST_END = 61, 110
N = CUST_END - CUST_START + 1
ACC_START, ACC_END = 161, 210
LOAN_START = CARD_START = CUST_START
LOAN_END = CARD_END = CUST_END
BEN_START, BEN_END = 16, 45

names = [
    ("Arjun Malhotra", "male", "India"), ("Meera Krishnan", "female", "India"), ("Kunal Desai", "male", "India"),
    ("Ishita Banerjee", "female", "India"), ("Aditya Chopra", "male", "India"), ("Riya Sen", "female", "India"),
    ("Nikhil Agarwal", "male", "India"), ("Pooja Verma", "female", "India"), ("Rahul Saxena", "male", "India"),
    ("Divya Menon", "female", "India"), ("Ethan Walker", "male", "USA"), ("Madison Price", "female", "USA"),
    ("Tyler Scott", "male", "USA"), ("Hannah Reed", "female", "USA"), ("Ryan Cooper", "male", "USA"),
    ("Ashley Turner", "female", "USA"), ("Justin Phillips", "male", "USA"), ("Lauren Campbell", "female", "USA"),
    ("Brandon Parker", "male", "USA"), ("Megan Evans", "female", "USA"), ("Daniel Wright", "male", "USA"),
    ("Chloe Adams", "female", "USA"), ("Matthew Hill", "male", "USA"), ("Benjamin King", "male", "UK"),
    ("Freya Scott", "female", "UK"), ("William Murphy", "male", "UK"), ("Grace Kelly", "female", "UK"),
    ("Henry Adams", "male", "UK"), ("Mia Campbell", "female", "UK"), ("Alexander Bell", "male", "UK"),
    ("Ella Patterson", "female", "UK"), ("Samuel Cook", "male", "UK"), ("Lily Foster", "female", "UK"),
    ("Finley Ross", "male", "UK"), ("Aria Bennett", "female", "UK"), ("Noah Fisher", "male", "USA"),
    ("Zoe Henderson", "female", "USA"), ("Logan Bennett", "male", "USA"), ("Natalie Collins", "female", "USA"),
    ("Caleb Murphy", "male", "USA"), ("Victoria Gray", "female", "USA"), ("Gabriel Ward", "male", "India"),
    ("Anika Ghosh", "female", "India"), ("Siddharth Bose", "male", "India"), ("Tara Khanna", "female", "India"),
    ("Varun Kapoor", "male", "India"), ("Neha Bhatia", "female", "India"), ("Karan Gill", "male", "India"),
    ("Shreya Dutta", "female", "India"), ("Manish Tiwari", "male", "India"),
]

assert len(names) == N

lines = []

vals = []
for idx, i in enumerate(range(CUST_START, CUST_END + 1)):
    name, gender, country = names[idx]
    age = random.randint(22, 55)
    salary = random.randint(30000, 150000)
    tenure = random.randint(1, 10)
    prd = random.randint(1, 5)
    cs = random.randint(580, 800)
    start = datetime(2018, 1, 1)
    end = datetime(2024, 6, 1)
    created = start + timedelta(days=random.randint(0, (end - start).days))
    vals.append(f"({i}, '{esc(name)}', {age}, '{gender}', '{country}', {d2(salary)}, {tenure}, {prd}, {cs}, '{created.date()}')")
lines.append("INSERT INTO Customer (customer_id, name, age, gender, country, salary, tenure, prd_number, credit_score, created_at) VALUES\n" + ",\n".join(vals) + ";")

acc_vals = []
for aid in range(ACC_START, ACC_END + 1):
    bid = random.choice([1, 2])
    atype = random.choice(["savings", "current"])
    bal = random.randint(5000, 150000) + random.random()
    status = "active" if random.random() < 0.9 else "closed"
    start = datetime(2019, 1, 1)
    end = datetime(2024, 1, 1)
    created = start + timedelta(days=random.randint(0, max(0, (end - start).days)))
    acc_vals.append(f"({aid}, {bid}, '{atype}', {d2(bal)}, '{status}', '{created.date()}')")
lines.append("INSERT INTO Account (account_id, branch_id, account_type, balance, status, created_at) VALUES\n" + ",\n".join(acc_vals) + ";")

secondary_accounts = {163, 171, 178, 186, 194, 201, 205, 209}
ah_vals = []
for aid in range(ACC_START, ACC_END + 1):
    cid = aid - 100
    ah_vals.append(f"({aid}, {cid}, 'primary')")
    if aid in secondary_accounts:
        sec = cid + 2 if cid <= CUST_END - 2 else cid - 2
        if sec == cid or sec < CUST_START or sec > CUST_END:
            sec = cid + 1 if cid < CUST_END else cid - 1
        ah_vals.append(f"({aid}, {sec}, 'secondary')")
lines.append("INSERT INTO Account_Holders (account_id, customer_id, role) VALUES\n" + ",\n".join(ah_vals) + ";")

cc_vals = []
for cid in range(CARD_START, CARD_END + 1):
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

all_accounts = list(range(101, ACC_END + 1))
txn_rows = []
for aid in range(ACC_START, ACC_END + 1):
    n = random.randint(10, 15)
    for _ in range(n):
        ttype = random.choices(["credit", "debit", "transfer"], weights=[0.3, 0.5, 0.2])[0]
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

loan_types = ["home", "car", "personal", "education"]
loan_vals = []
for lid in range(LOAN_START, LOAN_END + 1):
    cid = lid
    lt = random.choice(loan_types)
    amt = random.randint(50000, 800000) + random.random()
    ir = round(random.uniform(6.0, 12.0), 2)
    st = random.choice(["active", "closed"])
    loan_vals.append(f"({lid}, {cid}, '{lt}', {d2(amt)}, {d2(ir)}, '{st}')")
lines.append("INSERT INTO Loan (loan_id, customer_id, loan_type, amount, interest_rate, status) VALUES\n" + ",\n".join(loan_vals) + ";")

pay_vals = []
for lid in range(LOAN_START, LOAN_END + 1):
    pamt = random.randint(3000, 15000) + random.random()
    start = datetime(2024, 2, 1)
    end = datetime(2024, 12, 1)
    pd = start + timedelta(days=random.randint(0, (end - start).days))
    pay_vals.append(f"({lid}, {d2(pamt)}, '{pd.date()}')")
lines.append("INSERT INTO Loan_Payments (loan_id, amount, payment_date) VALUES\n" + ",\n".join(pay_vals) + ";")

issues = ["Card Issue", "Login Issue", "Fraud Alert", "Transfer Delay", "Loan Query", "App Crash", "Balance Issue"]
ticket_rows = []
for cid in range(CUST_START, CUST_END + 1):
    for _ in range(random.randint(1, 2)):
        it = random.choice(issues)
        desc = esc(f"Ticket detail: {it} — customer follow-up scheduled.")
        sent = random.choice(["positive", "neutral", "negative"])
        st = random.choice(["open", "closed"])
        cstart = datetime(2024, 1, 1)
        cend = datetime(2024, 12, 31, 23, 59, 59)
        created = cstart + timedelta(seconds=random.randint(0, int((cend - cstart).total_seconds())))
        if st == "closed":
            resolved = created + timedelta(days=random.randint(1, 3))
            res_s = f"'{resolved.strftime('%Y-%m-%d %H:%M:%S')}'"
        else:
            res_s = "NULL"
        ticket_rows.append(f"({cid}, '{it}', '{desc}', '{sent}', '{st}', '{created.strftime('%Y-%m-%d %H:%M:%S')}', {res_s})")
lines.append("INSERT INTO Support_Tickets (customer_id, issue_type, description, sentiment, status, created_at, resolved_at) VALUES\n" + ",\n".join(ticket_rows) + ";")

login_rows = []
for cid in range(CUST_START, CUST_END + 1):
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

own_account = {c: c + 100 for c in range(CUST_START, CUST_END + 1)}
ben_rows = []
for bid in range(BEN_START, BEN_END + 1):
    cid = random.randint(CUST_START, CUST_END)
    own = own_account[cid]
    choices = [a for a in all_accounts if a != own]
    bacc = random.choice(choices)
    ben_rows.append(f"({bid}, {cid}, {bacc})")
lines.append("INSERT INTO Beneficiary (beneficiary_id, customer_id, beneficiary_account) VALUES\n" + ",\n".join(ben_rows) + ";")

bs_vals = []
for cid in range(CUST_START, CUST_END + 1):
    tc = random.randint(5, 20)
    ab = random.randint(5000, 120000) + random.random()
    bdr = round(random.uniform(0.0, 0.50), 2)
    cc = random.randint(0, 5)
    lf = random.randint(1, 30)
    cl = random.choice([0, 1])
    bs_vals.append(f"({cid}, {tc}, {d2(ab)}, {d2(bdr)}, {cc}, {lf}, {cl})")
lines.append("INSERT INTO Behavior_Summary (customer_id, txn_count_30d, avg_balance, balance_drop_rate, complaint_count, login_frequency, churn_label) VALUES\n" + ",\n".join(bs_vals) + ";")

cp_vals = []
for cid in range(CUST_START, CUST_END + 1):
    rs = round(random.uniform(0.05, 0.95), 2)
    y0 = datetime(2024, 1, 1)
    y1 = datetime(2024, 12, 31, 23, 59, 59)
    lu = y0 + timedelta(seconds=random.randint(0, int((y1 - y0).total_seconds())))
    cp_vals.append(f"({cid}, {d2(rs)}, '{lu.strftime('%Y-%m-%d %H:%M:%S')}')")
lines.append("INSERT INTO Churn_Predictions (customer_id, risk_score, last_updated) VALUES\n" + ",\n".join(cp_vals) + ";")

out_path = "seed_extension_batch2.sql"
with open(out_path, "w", encoding="utf-8", newline="\n") as f:
    f.write("\n\n".join(lines))
    f.write("\n")

print("Wrote", out_path)
print("Customers:", N, "Transactions:", len(txn_rows), "Beneficiaries:", len(ben_rows))
