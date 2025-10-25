#!/usr/bin/env python3
"""
Regenerate employee directory from actual email addresses in database
Ensures HR directory matches the real sender/recipient emails
"""
import json
import random
import subprocess

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

def create_employee_from_email(email: str, emp_id: int) -> dict:
    """Create employee record from email address"""
    first_name = random.choice(FIRST_NAMES)
    last_name = random.choice(LAST_NAMES)
    department = random.choice(DEPARTMENTS)
    designation = random.choice(DESIGNATIONS[department])
    city = random.choice(CITIES)

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

def fetch_all_emails_from_database():
    """Fetch all unique sender and recipient emails from database"""
    print("Fetching emails from backend API...")

    all_senders = set()
    all_recipients = set()

    # Fetch emails in batches
    offset = 0
    limit = 100

    while True:
        # Use curl to fetch emails
        result = subprocess.run(
            ["curl", "-s", f"http://localhost:8000/api/emails?limit={limit}&offset={offset}"],
            capture_output=True,
            text=True
        )

        if result.returncode != 0:
            print(f"Error fetching emails: {result.stderr}")
            break

        try:
            emails = json.loads(result.stdout)
        except json.JSONDecodeError:
            print("Error parsing JSON response")
            break

        if not emails:
            break

        for email in emails:
            if email.get('sender'):
                all_senders.add(email['sender'])
            if email.get('recipient'):
                all_recipients.add(email['recipient'])

        print(f"  Processed {offset + len(emails)} emails...")
        offset += limit

        # Stop if we got fewer emails than requested
        if len(emails) < limit:
            break

    print(f"\nFound {len(all_senders)} unique senders")
    print(f"\nFound {len(all_recipients)} unique recipients")

    return all_senders, all_recipients

def main():
    """Main function"""
    print("=" * 60)
    print("REGENERATING EMPLOYEE DIRECTORY FROM DATABASE")
    print("=" * 60)

    # Fetch all unique emails from database
    senders, recipients = fetch_all_emails_from_database()

    # Combine all unique emails
    all_emails = sorted(senders | recipients)

    print(f"\nTotal unique email addresses: {len(all_emails)}")
    print("\nGenerating employee records...")

    # Generate employee records
    employees = []
    for i, email in enumerate(all_emails, 1):
        employee = create_employee_from_email(email, i)
        employees.append(employee)

        if i % 100 == 0:
            print(f"  Generated {i}/{len(all_emails)} employees...")

    # Save to employees.json
    output_file = "employees.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(employees, f, indent=2, ensure_ascii=False)

    print(f"\n✓ Generated {len(employees)} employees")
    print(f"✓ File saved: {output_file}")

    # Print sample
    print("\nSample employees:")
    for emp in employees[:5]:
        print(f"  {emp['employee_id']}: {emp['first_name']} {emp['last_name']} - {emp['email']} ({emp['department']})")

    print("\n" + "=" * 60)
    print("EMPLOYEE DIRECTORY REGENERATION COMPLETE!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Restart employee-directory service: docker compose restart employee-directory")
    print("2. Verify: curl http://localhost:8100/api/health")

if __name__ == "__main__":
    main()
