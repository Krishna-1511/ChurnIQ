"""One-off generator: run to produce customer_10000_insert.sql"""
import random

random.seed(12345)

GENDERS = ["male"] * 5500 + ["female"] * 4500
COUNTRIES = ["France"] * 5000 + ["Germany"] * 2500 + ["Spain"] * 2500
PRDS = [1] * 5000 + [2] * 4500 + [3] * 400 + [4] * 100
random.shuffle(GENDERS)
random.shuffle(COUNTRIES)
random.shuffle(PRDS)

FIRST_M = [
    "James", "Oliver", "William", "Lucas", "Henry", "Theo", "Leo", "Arthur", "Louis", "Gabriel",
    "Hugo", "Ethan", "Noah", "Liam", "Mason", "Luca", "Matteo", "Enzo", "Raphael", "Antoine",
    "Pierre", "Jean", "Marc", "Thomas", "Felix", "Jonas", "Maximilian", "Leon", "Niklas", "Sebastian",
    "Carlos", "Miguel", "Diego", "Pablo", "Antonio", "Manuel", "Raj", "Arjun", "Vikram", "Rohan",
    "Aditya", "Karan", "Rahul", "Dev", "Aryan", "Ishaan", "Vihaan", "Reyansh", "Shaurya", "Krish",
]
LAST = [
    "Martin", "Bernard", "Dubois", "Thomas", "Robert", "Richard", "Petit", "Durand", "Leroy", "Moreau",
    "Simon", "Laurent", "Lefebvre", "Michel", "Garcia", "Rodriguez", "Lopez", "Martinez", "Gonzalez",
    "Hernandez", "Mueller", "Schmidt", "Schneider", "Fischer", "Weber", "Meyer", "Wagner", "Becker",
    "Schulz", "Hoffmann", "Koch", "Richter", "Klein", "Wolf", "Schroeder", "Neumann", "Schwarz", "Braun",
    "Hofmann", "Zimmermann", "Kumar", "Sharma", "Patel", "Singh", "Reddy", "Iyer", "Nair", "Kapoor",
    "Malhotra", "Joshi", "Desai", "Mehta", "Verma", "Chopra", "Agarwal",
]
FIRST_F = [
    "Emma", "Olivia", "Amelia", "Isla", "Ava", "Mia", "Lily", "Sophia", "Grace", "Freya",
    "Ella", "Charlotte", "Chloe", "Sofia", "Camille", "Lea", "Manon", "Juliette", "Claire", "Elise",
    "Marie", "Anne", "Sophie", "Laura", "Nina", "Hannah", "Emilia", "Lena", "Clara", "Paula",
    "Lucia", "Elena", "Carmen", "Isabel", "Ana", "Priya", "Ananya", "Kavya", "Diya", "Isha",
    "Neha", "Riya", "Sneha", "Aisha", "Zara", "Meera", "Aditi", "Tanvi", "Kiara", "Pooja",
]


def pick_name(g: str) -> str:
    if g == "male":
        return f"{random.choice(FIRST_M)} {random.choice(LAST)}"
    return f"{random.choice(FIRST_F)} {random.choice(LAST)}"


def esc(s: str) -> str:
    return s.replace("'", "''")


rows = []
for cid in range(1, 10001):
    idx = cid - 1
    g = GENDERS[idx]
    country = COUNTRIES[idx]
    prd = PRDS[idx]
    random.seed(cid * 7919 + 42)
    name = pick_name(g)
    age = random.randint(18, 92)
    salary = round(random.uniform(11.58, 199992.48), 2)
    tenure = random.randint(0, 10)
    score = random.randint(350, 850)
    y = 2024 - tenure
    created = f"{y:04d}-01-01"
    rows.append(
        f"({cid},'{esc(name)}',{age},'{g}','{country}',{salary:.2f},{tenure},{prd},{score},'{created}')"
    )

sql = (
    "INSERT INTO Customer (customer_id, name, age, gender, country, salary, tenure, "
    "prd_number, credit_score, created_at) VALUES\n"
    + ",\n".join(rows)
    + ";\n"
)
with open("customer_10000_insert.sql", "w", encoding="utf-8") as f:
    f.write(sql)
print(len(rows), "rows -> customer_10000_insert.sql")
