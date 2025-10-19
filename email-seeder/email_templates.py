import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# Legitimate bank email templates (80%)
LEGITIMATE_TEMPLATES = [
    {
        "subject": "Your Monthly Bank Statement is Ready",
        "template": """Dear Valued Customer,

Your monthly statement for account ending in {account_num} is now available for viewing in your online banking portal.

Statement Period: {date_from} to {date_to}
Account Balance: ${balance}

To view your statement:
1. Log in to your account at https://www.bank.com
2. Navigate to Statements & Documents
3. Select the current month's statement

Thank you for banking with us.

Best regards,
{bank_name} Customer Service
""",
        "sender": "statements@customerservice.bank.com"
    },
    {
        "subject": "Transaction Alert: Withdrawal Confirmed",
        "template": """Dear Customer,

This is to confirm a recent transaction on your account ending in {account_num}.

Transaction Details:
Date: {transaction_date}
Type: Withdrawal
Amount: ${amount}
Location: {location}
Merchant: {merchant}

If you did not authorize this transaction, please contact us immediately at 1-800-BANK-HELP.

Thank you,
{bank_name} Security Team
""",
        "sender": "alerts@bank.com"
    },
    {
        "subject": "New Savings Account Benefits",
        "template": """Dear {customer_name},

We're pleased to announce enhanced benefits for your savings account!

New Features:
- Increased interest rate: {interest_rate}% APY
- No monthly maintenance fees
- Free ATM withdrawals nationwide
- Mobile check deposit

These benefits are automatically applied to your account ending in {account_num}.

Visit us at https://www.bank.com/savings to learn more.

Sincerely,
{bank_name} Team
""",
        "sender": "info@bank.com"
    },
    {
        "subject": "Appointment Confirmation - Branch Visit",
        "template": """Hello {customer_name},

This confirms your appointment at our {branch_location} branch:

Date: {appointment_date}
Time: {appointment_time}
Purpose: {appointment_reason}
Banker: {banker_name}

If you need to reschedule, please call us at 1-800-BANK-HELP or visit https://www.bank.com/appointments.

We look forward to seeing you!

{bank_name}
""",
        "sender": "appointments@bank.com"
    },
    {
        "subject": "Deposit Confirmation",
        "template": """Dear Customer,

A deposit has been made to your account ending in {account_num}.

Deposit Details:
Amount: ${amount}
Date: {transaction_date}
Type: {deposit_type}
New Balance: ${balance}

Thank you for banking with {bank_name}.

Customer Service
{bank_name}
""",
        "sender": "notifications@bank.com"
    },
    {
        "subject": "Credit Card Payment Received",
        "template": """Dear {customer_name},

We have received your credit card payment.

Payment Details:
Card ending in: {account_num}
Payment Amount: ${amount}
Payment Date: {transaction_date}
New Balance: ${balance}

Thank you for your payment.

{bank_name} Credit Card Services
""",
        "sender": "creditcard@bank.com"
    },
    {
        "subject": "Welcome to Mobile Banking!",
        "template": """Hello {customer_name},

Welcome to {bank_name} Mobile Banking! You've successfully enrolled and can now:

- Check balances and transactions
- Transfer money between accounts
- Pay bills
- Deposit checks with your camera
- Find nearby ATMs and branches

Download our app from the App Store or Google Play.

Need help? Visit https://www.bank.com/mobile-banking-guide

Thank you,
{bank_name} Digital Team
""",
        "sender": "mobile@bank.com"
    },
]

# Phishing email templates (20%)
PHISHING_TEMPLATES = [
    {
        "subject": "URGENT: Verify Your Account Immediately",
        "template": """Dear Customer,

We have detected unusual activity on your account. Your account has been temporarily suspended for your protection.

IMMEDIATE ACTION REQUIRED:

Click here to verify your identity: http://secure-bank-verify{random_num}.com/verify

You must verify within 24 hours or your account will be permanently locked.

Required Information:
- Full Account Number
- Social Security Number
- Online Banking Password
- Mother's Maiden Name

This is an automated security measure.

Security Department
{fake_bank_name}
""",
        "sender": "security@bank-alert{random_num}.com"
    },
    {
        "subject": "Action Required: Update Your Banking Information",
        "template": """Dear User,

Our system upgrade requires all customers to update their information.

Click here now: http://{random_num}-bankupdate.com/login

Failure to update within 48 hours will result in account suspension.

Please provide:
- Username and Password
- Account Number
- SSN
- Credit Card Details

Thank you for your immediate attention.

{fake_bank_name} IT Department
""",
        "sender": "noreply@bank{random_num}.com"
    },
    {
        "subject": "Suspicious Activity Detected - Confirm Now",
        "template": """ALERT: Unauthorized Login Attempt

Someone tried to access your account from {foreign_country}.

IP Address: {ip_address}
Time: {time}

If this wasn't you, click here immediately:
http://bit.ly/bank-security-{random_num}

Confirm your identity by entering:
- Full name and SSN
- Account and routing numbers
- Online banking credentials

Do not ignore this message!

Security Team
""",
        "sender": "security-alert@bank-protect{random_num}.com"
    },
    {
        "subject": "Your Account Has Been Locked",
        "template": """Dear Customer,

Your account ending in {account_num} has been locked due to suspicious activity.

To unlock your account, verify your identity here:
http://unlock-account-{random_num}.com

Enter your:
- Full account number
- PIN code
- Social Security Number
- Date of birth

This must be completed within 12 hours.

{fake_bank_name}
""",
        "sender": "account-services{random_num}@gmail.com"
    },
    {
        "subject": "Confirm Your Recent Transaction",
        "template": """Transaction Alert

A charge of ${large_amount} was attempted on your account.

Transaction Details:
Amount: ${large_amount}
Merchant: {suspicious_merchant}
Location: {foreign_country}

If you did not authorize this, click here:
http://tinyurl.com/bank{random_num}

You will need to provide:
- Your password
- Card number and CVV
- SSN for verification

Act now to prevent fraudulent charges!

Fraud Prevention Team
""",
        "sender": "fraud@bank-security{random_num}.net"
    },
    {
        "subject": "Verify Account or Face Closure",
        "template": """FINAL NOTICE

Your account will be closed in 24 hours unless you verify your information.

Verify now: http://{ip_address}/verify-account

Due to new banking regulations, we need:
- Account number and routing number
- Online banking password
- SSN and driver's license number

This is your last warning before permanent account closure.

Compliance Department
{fake_bank_name}
""",
        "sender": "compliance@banking-update{random_num}.com"
    },
]

def generate_legitimate_email():
    """Generate a legitimate banking email"""
    template = random.choice(LEGITIMATE_TEMPLATES)

    customer_name = fake.name()
    account_num = str(random.randint(1000, 9999))
    balance = round(random.uniform(100, 50000), 2)
    amount = round(random.uniform(10, 5000), 2)

    date_from = datetime.now() - timedelta(days=30)
    date_to = datetime.now()
    transaction_date = datetime.now() - timedelta(days=random.randint(0, 7))

    body = template["template"].format(
        customer_name=customer_name,
        account_num=account_num,
        date_from=date_from.strftime("%Y-%m-%d"),
        date_to=date_to.strftime("%Y-%m-%d"),
        balance=f"{balance:,.2f}",
        amount=f"{amount:,.2f}",
        transaction_date=transaction_date.strftime("%Y-%m-%d %H:%M"),
        location=fake.city(),
        merchant=fake.company(),
        bank_name="First National Bank",
        interest_rate=round(random.uniform(0.5, 3.5), 2),
        branch_location=fake.city(),
        appointment_date=(datetime.now() + timedelta(days=random.randint(1, 14))).strftime("%Y-%m-%d"),
        appointment_time=f"{random.randint(9, 16)}:00",
        appointment_reason=random.choice(["Account Review", "Loan Application", "Investment Consultation"]),
        banker_name=fake.name(),
        deposit_type=random.choice(["Direct Deposit", "Check Deposit", "Wire Transfer"])
    )

    return {
        "subject": template["subject"],
        "sender": template["sender"],
        "body": body,
        "is_phishing": False
    }

def generate_phishing_email():
    """Generate a phishing email"""
    template = random.choice(PHISHING_TEMPLATES)

    random_num = random.randint(1000, 9999)
    large_amount = round(random.uniform(500, 5000), 2)

    body = template["template"].format(
        random_num=random_num,
        fake_bank_name=random.choice(["Bank of America", "Wells Fargo", "Chase Bank", "CitiBank"]),
        foreign_country=random.choice(["Russia", "China", "Nigeria", "Romania"]),
        ip_address=fake.ipv4(),
        time=datetime.now().strftime("%Y-%m-%d %H:%M"),
        account_num=str(random.randint(1000, 9999)),
        large_amount=f"{large_amount:,.2f}",
        suspicious_merchant=random.choice(["Unknown Merchant", "Foreign Electronics", "Overseas Wire Transfer"])
    )

    return {
        "subject": template["subject"],
        "sender": template["sender"],
        "body": body,
        "is_phishing": True
    }

def generate_email():
    """Generate either a legitimate or phishing email based on 80/20 split"""
    if random.random() < 0.80:  # 80% legitimate
        return generate_legitimate_email()
    else:  # 20% phishing
        return generate_phishing_email()
