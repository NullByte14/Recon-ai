import pandas as pd
import random
from datetime import datetime, timedelta
import os

def generate_sample_data():
    os.makedirs('data', exist_ok=True)
    
    # Base transactions that match perfectly (25 items)
    base_data = [
        {"description": "Office Supplies - Staples", "amount": -150.00, "category": "Office Expense"},
        {"description": "Client Payment - Acme Corp", "amount": 2500.00, "category": "Revenue"},
        {"description": "Payroll - March", "amount": -8500.00, "category": "Payroll"},
        {"description": "Software Subscription - Adobe", "amount": -54.99, "category": "Software"},
        {"description": "AWS Cloud Hosting", "amount": -320.15, "category": "Software"},
        {"description": "Client Payment - Beta LLC", "amount": 1200.00, "category": "Revenue"},
        {"description": "Internet - Comcast", "amount": -110.00, "category": "Utilities"},
        {"description": "Office Rent", "amount": -2000.00, "category": "Rent"},
        {"description": "Cleaning Service", "amount": -250.00, "category": "Maintenance"},
        {"description": "Coffee & Snacks", "amount": -85.50, "category": "Office Expense"},
        {"description": "Marketing - Google Ads", "amount": -500.00, "category": "Marketing"},
        {"description": "Marketing - LinkedIn", "amount": -300.00, "category": "Marketing"},
        {"description": "Client Payment - Gamma Inc", "amount": 3400.00, "category": "Revenue"},
        {"description": "Legal Consultation", "amount": -600.00, "category": "Legal"},
        {"description": "Accounting Services", "amount": -400.00, "category": "Accounting"},
        {"description": "Travel - Delta Airlines", "amount": -450.00, "category": "Travel"},
        {"description": "Hotel - Marriott", "amount": -380.00, "category": "Travel"},
        {"description": "Uber Rides", "amount": -45.00, "category": "Travel"},
        {"description": "Client Dinner", "amount": -120.00, "category": "Meals"},
        {"description": "Team Lunch", "amount": -150.00, "category": "Meals"},
        {"description": "Client Payment - Delta Co", "amount": 1800.00, "category": "Revenue"},
        {"description": "Equipment - Dell Monitors", "amount": -600.00, "category": "Equipment"},
        {"description": "Software - Slack", "amount": -80.00, "category": "Software"},
        {"description": "Software - Zoom", "amount": -40.00, "category": "Software"},
        {"description": "Client Payment - Epsilon Ltd", "amount": 2100.00, "category": "Revenue"}
    ]

    start_date = datetime(2023, 3, 1)
    
    ledger_records = []
    bank_records = []
    
    def add_record(desc, amt, cat, days_offset, t_id_prefix="TX"):
        date_str = (start_date + timedelta(days=days_offset)).strftime("%Y-%m-%d")
        t_id = f"{t_id_prefix}{random.randint(10000, 99999)}"
        return {"transaction_id": t_id, "date": date_str, "description": desc, "amount": amt, "category": cat}

    # 1. 25 perfect matches
    for i, item in enumerate(base_data):
        days = random.randint(0, 28)
        rec = add_record(item["description"], item["amount"], item["category"], days)
        # Bank uses the exact same record, maybe slight different ID doesn't matter for matching, but we'll use same logic
        ledger_records.append(rec.copy())
        # Let's give bank slightly different transaction_ids just for realism, matching shouldn't rely on it
        bank_rec = rec.copy()
        bank_rec["transaction_id"] = f"BNK{random.randint(10000, 99999)}"
        bank_records.append(bank_rec)

    # 2. 5 transactions present in ledger but missing from bank (Timing Differences)
    for i in range(5):
        rec = add_record(f"Vendor Payment - Check {100+i}", -random.randint(100, 500), "Vendor", 28 + i)
        ledger_records.append(rec)

    # 3. 5 transactions present in bank but missing from ledger
    bank_only = [
        {"desc": "Monthly Account Maintenance Fee", "amt": -25.00, "cat": "Bank Fees"},
        {"desc": "Wire Transfer Fee", "amt": -15.00, "cat": "Bank Fees"},
        {"desc": "Interest Paid", "amt": 12.50, "cat": "Interest"},
        {"desc": "Unrecorded Auto-Debit - Insurance", "amt": -200.00, "cat": "Insurance"},
        {"desc": "Overdraft Fee", "amt": -35.00, "cat": "Bank Fees"}
    ]
    for item in bank_only:
        bank_rec = add_record(item["desc"], item["amt"], item["cat"], random.randint(1, 28), "BNK")
        bank_records.append(bank_rec)

    # 4. 3 transactions with matching date/desc but different amounts (Data entry errors)
    mismatch_data = [
        {"desc": "Office Supplies - Paper", "l_amt": -105.00, "b_amt": -150.00, "cat": "Office Expense"},
        {"desc": "Client Payment - Late", "l_amt": 500.00, "b_amt": 505.00, "cat": "Revenue"},
        {"desc": "Contractor Payment", "l_amt": -1000.00, "b_amt": -1000.50, "cat": "Contractor"}
    ]
    for item in mismatch_data:
        days = random.randint(1, 28)
        date_str = (start_date + timedelta(days=days)).strftime("%Y-%m-%d")
        
        l_rec = {"transaction_id": f"TX{random.randint(10000, 99999)}", "date": date_str, "description": item["desc"], "amount": item["l_amt"], "category": item["cat"]}
        b_rec = {"transaction_id": f"BNK{random.randint(10000, 99999)}", "date": date_str, "description": item["desc"], "amount": item["b_amt"], "category": item["cat"]}
        
        ledger_records.append(l_rec)
        bank_records.append(b_rec)

    # 5. 2 duplicate entries in the ledger
    # Pick two of the perfect matches and add them again to the ledger
    for i in range(2):
        dup_rec = ledger_records[i].copy()
        dup_rec["transaction_id"] = f"TX{random.randint(10000, 99999)}"
        ledger_records.append(dup_rec)

    # Shuffle both lists
    random.shuffle(ledger_records)
    random.shuffle(bank_records)

    # Save to CSV
    pd.DataFrame(ledger_records).to_csv('data/ledger_sample.csv', index=False)
    pd.DataFrame(bank_records).to_csv('data/bank_statement_sample.csv', index=False)
    
    print("Sample data generated successfully in data/ directory.")
    print(f"Ledger records: {len(ledger_records)}")
    print(f"Bank records: {len(bank_records)}")

if __name__ == "__main__":
    generate_sample_data()
