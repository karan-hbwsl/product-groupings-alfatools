import os
import re
import pdfplumber
import pandas as pd
from groq import Groq
from dotenv import load_dotenv
from io import StringIO

load_dotenv()
client = Groq(api_key=os.getenv("GROQ_API_KEY"))

def extract_page_texts(pdf_path, start_page=0, end_page=None):
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        pages = pdf.pages[start_page:end_page]
        for i, page in enumerate(pages, start=start_page):
            text = page.extract_text()
            if text:
                pages_text.append((i + 1, text))
    return pages_text

def ask_groq_for_tables_from_page(page_number, text):
    system_prompt = "You are a data assistant. Extract all tables from the following PDF page text. Return each table as clean CSVs. If multiple tables exist, return each table with a title like 'Table X: Title', followed by the CSV."

    user_prompt = f"""Extract all tables from this page and return them as clean CSVs (include headers and rows).

--- PAGE {page_number} TEXT START ---
{text.strip()}
--- PAGE TEXT END ---

Return the output as:

**Table 1: Table Name**
<CSV>

**Table 2: Table Name**
<CSV>

Do not include explanations.
"""

    try:
        response = client.chat.completions.create(
            model="llama3-70b-8192",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        print(f"⚠️ Groq Error on page {page_number}:", e)
        return None

def sanitize_filename(name):
    return re.sub(r'[\\/*?:"<>|]', "", name).strip()

def split_and_save_csvs_from_response(csv_text, page_number):
    sections = re.split(r'\*\*Table\s+\d+:\s*(.*?)\*\*', csv_text)

    if len(sections) < 3:
        print(f"⚠️ No valid tables found on page {page_number}")
        return

    os.makedirs("tables", exist_ok=True)  # ✅ Ensure output folder exists

    for i in range(1, len(sections) - 1, 2):
        title = sanitize_filename(sections[i])
        csv_block = sections[i + 1].strip()

        try:
            df = pd.read_csv(StringIO(csv_block))
            filename = os.path.join("tables", f"Page-{page_number}-{title}.csv")  # ✅ Save in tables/
            df.to_csv(filename, index=False)
            print(f"✅ Saved: {filename}")
        except Exception as e:
            print(f"⚠️ Failed to save '{title}' on page {page_number}: {e}")

def process_pdf_whole_page_text(pdf_path, start_page=0, end_page=None):
    pages = extract_page_texts(pdf_path, start_page, end_page)
    print(f"📄 Processing {len(pages)} pages")

    for page_num, text in pages:
        print(f"\n🔍 Sending page {page_num} to Groq...")
        csv_text = ask_groq_for_tables_from_page(page_num, text)
        if csv_text:
            split_and_save_csvs_from_response(csv_text, page_num)

# Run the script
process_pdf_whole_page_text("publication.pdf", start_page=300, end_page=306)
