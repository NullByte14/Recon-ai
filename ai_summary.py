import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Models to try in order — prioritizing confirmed working models
FALLBACK_MODELS = [
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.7-flash",
    "gemini-3.8-flash",
]

def generate_summary(flagged_df):
    """
    Sends the flagged reconciliation transactions to Gemini and returns a summary.
    Uses the google-genai SDK with automatic model fallback.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    
    if not api_key or api_key == "your_api_key_here":
         return "⚠️ **API Key Missing**: Please set your `GEMINI_API_KEY` in the `.env` file to generate AI summaries."
         
    try:
        from google import genai

        client = genai.Client(api_key=api_key)
        
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
        
        prompt = f"{system_prompt}\n\nData Context:\n{context_str}"
        
        # Try each model in the fallback list
        last_error = None
        for model_name in FALLBACK_MODELS:
            try:
                response = client.models.generate_content(
                    model=model_name,
                    contents=prompt
                )
                return response.text
            except Exception as model_err:
                last_error = model_err
                continue  # Try the next model
        
        # If all models failed, return the last error
        return f"⚠️ **Error generating AI summary**: All models unavailable. Last error: {str(last_error)}"
        
    except Exception as e:
        return f"⚠️ **Error generating AI summary**: {str(e)}"
