import pandas as pd
from datetime import timedelta
import difflib

def reconcile(ledger_df, bank_df):
    """
    Reconciles ledger and bank statement DataFrames.
    Returns a combined DataFrame with status and notes, and summary statistics.
    """
    # Ensure date columns are datetime objects, ignoring time for exact matching
    ledger_df['date'] = pd.to_datetime(ledger_df['date']).dt.normalize()
    bank_df['date'] = pd.to_datetime(bank_df['date']).dt.normalize()
    
    # Add source tracking and initialize status
    ledger = ledger_df.copy()
    bank = bank_df.copy()
    
    ledger['source'] = 'Ledger'
    bank['source'] = 'Bank'
    
    ledger['status'] = 'Unmatched - Ledger Only'
    bank['status'] = 'Unmatched - Bank Only'
    
    ledger['notes'] = ''
    bank['notes'] = ''
    
    # Track matched indices to avoid double matching
    matched_ledger_idx = set()
    matched_bank_idx = set()

    # Step 1: Detect duplicates within Ledger
    # A simple approach: group by date, amount, description
    ledger_dups = ledger[ledger.duplicated(subset=['date', 'amount', 'description'], keep=False)]
    for idx in ledger_dups.index:
        ledger.at[idx, 'status'] = 'Possible Duplicate'
        ledger.at[idx, 'notes'] = 'Exact same date, amount, and description found multiple times in ledger'
        # Optional: We could exclude them from further matching or try to match one of them.
        # We will attempt to match one, but label the other as duplicate.
        # Actually, let's keep it simple: mark all as Possible Duplicate, but still let exact match claim one if possible.

    # Re-evaluating duplicate logic:
    # We will identify duplicates, mark them, but we don't necessarily exclude them.
    # To follow requirements strictly, let's just do matching.

    # Step 2: Exact Match (Amount and Date)
    for l_idx, l_row in ledger.iterrows():
        if l_idx in matched_ledger_idx:
            continue
            
        # Find exact matches in bank
        exact_matches = bank[
            (bank['amount'] == l_row['amount']) & 
            (bank['date'] == l_row['date']) & 
            (~bank.index.isin(matched_bank_idx))
        ]
        
        if not exact_matches.empty:
            b_idx = exact_matches.index[0]
            matched_ledger_idx.add(l_idx)
            matched_bank_idx.add(b_idx)
            
            ledger.at[l_idx, 'status'] = 'Matched'
            ledger.at[l_idx, 'notes'] = 'Exact match on date and amount'
            
            bank.at[b_idx, 'status'] = 'Matched'
            bank.at[b_idx, 'notes'] = 'Exact match on date and amount'

    # Step 3: Fuzzy Matching for remaining
    for l_idx, l_row in ledger.iterrows():
        if l_idx in matched_ledger_idx:
            continue
            
        remaining_bank = bank[~bank.index.isin(matched_bank_idx)]
        if remaining_bank.empty:
            break
            
        best_match_idx = None
        match_type = None
        
        for b_idx, b_row in remaining_bank.iterrows():
            # Condition A: Same amount within ±2 days (Timing Difference)
            date_diff = abs((l_row['date'] - b_row['date']).days)
            if l_row['amount'] == b_row['amount'] and date_diff <= 2:
                best_match_idx = b_idx
                match_type = 'Timing Difference'
                break # Prioritize timing difference
                
            # Condition B: Same date with amount within ±$0.01 (Rounding)
            if l_row['date'] == b_row['date'] and abs(l_row['amount'] - b_row['amount']) <= 0.01:
                best_match_idx = b_idx
                match_type = 'Matched'
                break
                
            # Condition C: Similar description (threshold 0.6) with matching amount (Timing Difference or matched if same date)
            # Or matching date/description but amount differs (Amount Mismatch)
            if l_row['date'] == b_row['date'] and l_row['amount'] != b_row['amount']:
                # Same date, check description
                similarity = difflib.SequenceMatcher(None, str(l_row['description']).lower(), str(b_row['description']).lower()).ratio()
                if similarity >= 0.6:
                    best_match_idx = b_idx
                    match_type = 'Amount Mismatch'
                    break
            
            # Same amount, check description (Timing difference if dates are far)
            if l_row['amount'] == b_row['amount']:
                similarity = difflib.SequenceMatcher(None, str(l_row['description']).lower(), str(b_row['description']).lower()).ratio()
                if similarity >= 0.6:
                    best_match_idx = b_idx
                    match_type = 'Timing Difference'
                    break
        
        if best_match_idx is not None:
            matched_ledger_idx.add(l_idx)
            matched_bank_idx.add(best_match_idx)
            
            ledger.at[l_idx, 'status'] = match_type
            bank.at[best_match_idx, 'status'] = match_type
            
            if match_type == 'Timing Difference':
                note = 'Matched on amount/description, but dates differ'
            elif match_type == 'Amount Mismatch':
                note = f"Matched on date/description, but amount differs (Ledger: {l_row['amount']}, Bank: {bank.at[best_match_idx, 'amount']})"
            else:
                note = 'Matched with slight variance'
                
            ledger.at[l_idx, 'notes'] = note
            bank.at[best_match_idx, 'notes'] = note

    # Check for possible duplicates strictly based on remaining unmatched or even matched if they are duplicated in ledger
    # Actually, a better duplicate check: 
    # If there are identical rows in ledger and one is unmatched, mark unmatched as duplicate.
    ledger_duplicates = ledger[ledger.duplicated(subset=['date', 'amount', 'description'], keep=False)]
    for idx in ledger_duplicates.index:
        if ledger.at[idx, 'status'] == 'Unmatched - Ledger Only':
            ledger.at[idx, 'status'] = 'Possible Duplicate'
            ledger.at[idx, 'notes'] = 'This appears to be a duplicate entry in the ledger'

    # Combine DataFrames
    combined_df = pd.concat([ledger, bank], ignore_index=True)
    
    # Sort for better readability
    combined_df = combined_df.sort_values(by=['date', 'amount'])
    
    # Calculate summary stats
    total_tx = len(combined_df)
    matched_count = len(combined_df[combined_df['status'] == 'Matched'])
    
    flagged_df = combined_df[combined_df['status'] != 'Matched']
    flagged_count = len(flagged_df)
    
    # Value of discrepancies (sum of absolute amounts of unmatched/mismatched items)
    # Be careful not to double count. Let's just sum absolute amounts of all non-matched items.
    # Actually, for amount mismatch, it's the difference. For unmatched, it's the full amount.
    discrepancy_value = 0.0
    
    for _, row in flagged_df.iterrows():
        if row['status'] in ['Unmatched - Ledger Only', 'Unmatched - Bank Only', 'Possible Duplicate', 'Timing Difference']:
            discrepancy_value += abs(row['amount'])
        elif row['status'] == 'Amount Mismatch' and row['source'] == 'Ledger':
             # We just need a rough number, summing absolute values of ledger mismatches might be easier
             pass

    # A simpler metric: Total absolute value of all flagged transactions
    total_discrepancy_value = flagged_df['amount'].abs().sum()
    
    summary = {
        "Total Transactions": total_tx,
        "Matched": matched_count,
        "Flagged": flagged_count,
        "Total Discrepancy Value (₹)": round(total_discrepancy_value, 2)
    }
    
    return combined_df, summary
