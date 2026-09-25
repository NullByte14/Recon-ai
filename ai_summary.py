import os
import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def generate_summary(flagged_df):
    """
    Sends the flagged reconciliation transactions to Gemini and returns a summary.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_api_key_here":
         return "⚠️ **API Key Missing**: Please set your `GEMINI_API_KEY` in the `.env` file to generate AI summaries."
         
    try:
        genai.configure(api_key=api_key)
        # Using gemini-2.0-flash as requested
        model = genai.GenerativeModel("gemini-2.0-flash")
        
        # Prepare the context to avoid hitting token limits
        # We group by status and summarize counts, plus a few examples
        context_str = ""
        grouped = flagged_df.groupby('status')
        
        for status, group in grouped:
            context_str += f"Status: {status} (Count: {len(group)})\n"
            # Add up to 3 examples per category
            examples = group.head(3)
            for _, row in examples.iterrows():
                context_str += f"- Date: {row['date'].strftime('%Y-%m-%d') if hasattr(row['date'], 'strftime') else row['date']}, "
                context_str += f"Source: {row['source']}, Amount: {row['amount']}, "
                context_str += f"Desc: {row['description']}, Notes: {row['notes']}\n"
            context_str += "\n"
            
        system_prompt = (
            "You are a financial analyst assistant helping a finance team understand "
            "reconciliation discrepancies between their internal ledger and bank "
            "statement. You will be given a list of flagged transactions with their "
            "status (Timing Difference, Amount Mismatch, Unmatched - Ledger Only, "
            "Unmatched - Bank Only, Possible Duplicate). For each category present, "
            "write a short, clear explanation in plain English of what likely caused "
            "these discrepancies and what the finance team should check or do next. "
            "Keep the tone professional and concise, like a summary you'd put in a "
            "management report. Use markdown with headers per category. Do not just "
            "repeat the raw data back — provide analysis and next steps."
        )
        
        response = model.generate_content(f"{system_prompt}\n\nData Context:\n{context_str}")
        return response.text
        
    except Exception as e:
        return f"⚠️ **Error generating AI summary**: {str(e)}"
