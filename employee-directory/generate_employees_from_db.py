#!/usr/bin/env python3
"""
Generate employee directory from emails in database
Fetches all unique sender/recipient emails and creates Swiss bank employee profiles
"""
import json
import os
import random
import subprocess
import sys

# Swiss data
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

CITIES = [
    "Zürich", "Geneva", "Basel", "Bern", "Lausanne", "Winterthur", "Lucerne",
    "St. Gallen", "Lugano", "Biel/Bienne", "Thun", "Köniz", "La Chaux-de-Fonds",
    "Fribourg", "Schaffhausen", "Vernier", "Chur", "Neuchâtel", "Uster", "Sion"
]

STREET_NAMES = [
    "Bahnhofstrasse", "Hauptstrasse", "Dorfstrasse", "Schulstrasse", "Kirchweg",
    "Bergstrasse", "Seestrasse", "Talstrasse", "Gartenweg", "Lindenhof",
    "Rebbergstrasse", "Feldweg", "Waldstrasse", "Mühleweg", "Brunnenplatz"
]

DEPARTMENTS = [
    "Private Banking", "Wealth Management", "Investment Banking", "Retail Banking",
    "Corporate Banking", "Asset Management", "Risk Management", "Compliance",
    "IT & Digital", "Human Resources", "Legal", "Finance & Accounting",
    "Customer Service", "Operations", "Treasury", "Credit & Loans"
]

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

def generate_phone():
    prefix = random.choice(["044", "031", "061", "021", "022", "041", "071"])
    return f"+41 {prefix} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"

def generate_mobile():
    prefix = random.choice(["76", "77", "78", "79"])
    return f"+41 {prefix} {random.randint(100, 999)} {random.randint(10, 99)} {random.randint(10, 99)}"

def fetch_emails_from_backend():
    """Fetch all unique emails from backend API in batches"""
    print("Fetching emails from backend API...")

    all_senders = set()
    all_recipients = set()
    offset = 0
    limit = 100

    while True:
        # Use curl to fetch emails
        result = subprocess.run(
            ["curl", "-s", f"http://backend:8000/api/emails?limit={limit}&offset={offset}"],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            print(f"Error fetching emails: {result.stderr}")
            break

        try:
            emails = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            break

        if not emails or not isinstance(emails, list):
            break

        for email in emails:
            if email.get('sender'):
                all_senders.add(email['sender'])
            if email.get('recipient'):
                all_recipients.add(email['recipient'])

        print(f"  Processed {offset + len(emails)} emails...")
        offset += limit

        if len(emails) < limit:
            break

    print(f"Found {len(all_senders)} unique senders")
    print(f"Found {len(all_recipients)} unique recipients")

    return all_senders, all_recipients

def main():
    print("=" * 60)
    print("GENERATING EMPLOYEE DIRECTORY FROM DATABASE")
    print("=" * 60)

    # Ensure data directory exists
    data_dir = "/app/data"
    os.makedirs(data_dir, exist_ok=True)
    employees_file = os.path.join(data_dir, "employees.json")

    try:
        # Fetch all unique emails
        senders, recipients = fetch_emails_from_backend()
        all_emails = sorted(senders | recipients)

        if not all_emails:
            print("WARNING: No emails found in database!")
            print("Creating empty employee directory")
            with open(employees_file, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
            return

        print(f"\nTotal unique emails: {len(all_emails)}")
        print("Generating employee records...")

        # Generate employee records
        employees = []
        for i, email in enumerate(all_emails, 1):
            dept = random.choice(DEPARTMENTS)
            employee = {
                "employee_id": f"SB{i:05d}",
                "first_name": random.choice(FIRST_NAMES),
                "last_name": random.choice(LAST_NAMES),
                "email": email,
                "mobile": generate_mobile(),
                "phone": generate_phone(),
                "department": dept,
                "designation": random.choice(DESIGNATIONS[dept]),
                "address": f"{random.choice(STREET_NAMES)} {random.randint(1, 150)}",
                "city": random.choice(CITIES),
                "country": "Switzerland"
            }
            employees.append(employee)

            if i % 1000 == 0:
                print(f"  Generated {i}/{len(all_emails)} employees...")

        # Save to employees.json in data directory
        with open(employees_file, "w", encoding="utf-8") as f:
            json.dump(employees, f, indent=2, ensure_ascii=False)

        print(f"\n✓ Generated {len(employees)} employees")
        print(f"✓ File saved: {employees_file}")
        print("=" * 60)

    except Exception as e:
        print(f"ERROR: Failed to generate employee directory: {e}")
        print("Creating empty employee directory as fallback")
        with open(employees_file, "w", encoding="utf-8") as f:
            json.dump([], f, indent=2)
        sys.exit(1)

if __name__ == "__main__":
    main()
