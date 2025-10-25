"""
Generate synthetic employee data for a Swiss bank
Matches the email dataset customer patterns
"""
import json
import random

# Swiss-appropriate first and last names
FIRST_NAMES = [
    "Hans", "Peter", "Markus", "Thomas", "Andreas", "Martin", "Stefan", "Daniel",
    "Michael", "Patrick", "Christian", "Marcel", "Reto", "Lukas", "Simon", "David",
    "Nicole", "Sandra", "Andrea", "Claudia", "Barbara", "Petra", "Martina", "Stefanie",
    "Simone", "Sabine", "Monika", "Daniela", "Katrin", "Anna", "Laura", "Sarah",
    "Beat", "René", "Urs", "Fritz", "Walter", "Bruno", "Franz", "Heinrich",
    "Isabella", "Maria", "Elisabeth", "Sophia", "Emma", "Mia", "Julia", "Lea"
]

LAST_NAMES = [
    "Müller", "Meier", "Schmid", "Keller", "Weber", "Huber", "Schneider", "Meyer",
    "Steiner", "Fischer", "Gerber", "Brunner", "Baumann", "Frei", "Zimmermann",
    "Moser", "Widmer", "Graf", "Wyss", "Kaufmann", "Herzog", "Sutter", "Roth",
    "Maurer", "Lehmann", "Imhof", "Bieri", "Hofmann", "Nussbaum", "Stettler"
]

# Swiss cities
CITIES = [
    "Zürich", "Geneva", "Basel", "Bern", "Lausanne", "Winterthur", "Lucerne",
    "St. Gallen", "Lugano", "Biel/Bienne", "Thun", "Köniz", "La Chaux-de-Fonds",
    "Fribourg", "Schaffhausen", "Vernier", "Chur", "Neuchâtel", "Uster", "Sion"
]

# Street names (Swiss-style)
STREET_NAMES = [
    "Bahnhofstrasse", "Hauptstrasse", "Dorfstrasse", "Schulstrasse", "Kirchweg",
    "Bergstrasse", "Seestrasse", "Talstrasse", "Gartenweg", "Lindenhof",
    "Rebbergstrasse", "Feldweg", "Waldstrasse", "Mühleweg", "Brunnenplatz"
]

# Departments
DEPARTMENTS = [
    "Private Banking", "Wealth Management", "Investment Banking", "Retail Banking",
    "Corporate Banking", "Asset Management", "Risk Management", "Compliance",
    "IT & Digital", "Human Resources", "Legal", "Finance & Accounting",
    "Customer Service", "Operations", "Treasury", "Credit & Loans"
]

# Designations
DESIGNATIONS = {
    "Private Banking": ["Private Banker", "Senior Relationship Manager", "Client Advisor", "Portfolio Manager"],
    "Wealth Management": ["Wealth Manager", "Financial Advisor", "Investment Consultant", "Family Office Manager"],
    "Investment Banking": ["Investment Banker", "M&A Analyst", "Equity Research Analyst", "Trader"],
    "Retail Banking": ["Branch Manager", "Customer Relationship Manager", "Loan Officer", "Teller Supervisor"],
    "Corporate Banking": ["Corporate Banker", "Credit Analyst", "Business Development Manager", "Relationship Manager"],
    "Asset Management": ["Fund Manager", "Portfolio Analyst", "Investment Strategist", "Asset Allocation Specialist"],
    "Risk Management": ["Risk Manager", "Compliance Officer", "Risk Analyst", "Credit Risk Officer"],
    "Compliance": ["Compliance Manager", "AML Specialist", "Regulatory Affairs Manager", "KYC Analyst"],
    "IT & Digital": ["IT Manager", "Software Engineer", "Cybersecurity Analyst", "Digital Banking Specialist"],
    "Human Resources": ["HR Manager", "Talent Acquisition Specialist", "HR Business Partner", "Learning & Development Manager"],
    "Legal": ["Legal Counsel", "Contracts Manager", "Regulatory Lawyer", "Legal Advisor"],
    "Finance & Accounting": ["Financial Controller", "Accountant", "Financial Analyst", "Audit Manager"],
    "Customer Service": ["Customer Service Manager", "Client Support Specialist", "Call Center Manager", "Service Quality Manager"],
    "Operations": ["Operations Manager", "Process Manager", "Operations Analyst", "Back Office Manager"],
    "Treasury": ["Treasury Manager", "Cash Management Specialist", "Liquidity Manager", "Treasury Analyst"],
    "Credit & Loans": ["Credit Manager", "Loan Officer", "Credit Analyst", "Mortgage Specialist"]
}

def generate_swiss_phone():
    """Generate a Swiss phone number"""
    prefix = random.choice(["044", "031", "061", "021", "022", "041", "071"])
    number = f"{random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"
    return f"+41 {prefix} {number}"

def generate_mobile():
    """Generate a Swiss mobile number"""
    prefix = random.choice(["76", "77", "78", "79"])
    number = f"{random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"
    return f"+41 {prefix} {number}"

def generate_address():
    """Generate a Swiss address"""
    street = random.choice(STREET_NAMES)
    number = random.randint(1, 150)
    return f"{street} {number}"

def generate_employee(emp_id):
    """Generate a single employee"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    department = random.choice(DEPARTMENTS)
    designation = random.choice(DESIGNATIONS[department])
    city = random.choice(CITIES)

    # Generate email - use Swiss bank domain
    email_name = f"{first_name.lower()}.{last_name.lower()}".replace("ü", "u").replace("ö", "o").replace("ä", "a")
    email = f"{email_name}@swissbank.ch"

    return {
        "employee_id": f"SB{emp_id:05d}",
        "first_name": first_name,
        "last_name": last_name,
        "email": email,
        "mobile": generate_mobile(),
        "phone": generate_swiss_phone(),
        "department": department,
        "designation": designation,
        "address": generate_address(),
        "city": city,
        "country": "Switzerland"
    }

def generate_dataset(count=200):
    """Generate employee dataset"""
    employees = []
    used_emails = set()

    emp_id = 1
    while len(employees) < count:
        employee = generate_employee(emp_id)

        # Ensure unique emails
        if employee["email"] not in used_emails:
            employees.append(employee)
            used_emails.add(employee["email"])
            emp_id += 1

    return employees

if __name__ == "__main__":
    print("Generating Swiss Bank employee directory...")
    employees = generate_dataset(200)

    with open("employees.json", "w", encoding="utf-8") as f:
        json.dump(employees, f, indent=2, ensure_ascii=False)

    print(f"✓ Generated {len(employees)} employees")
    print(f"✓ Departments: {len(DEPARTMENTS)}")
    print(f"✓ File saved: employees.json")

    # Print sample
    print("\nSample employees:")
    for emp in employees[:5]:
        print(f"  {emp['employee_id']}: {emp['first_name']} {emp['last_name']} ({emp['department']}) - {emp['mobile']}")
