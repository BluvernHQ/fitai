import pandas as pd
import json
import os
import re

# CONFIGURATION
INPUT_EXCEL_PATH = 'data/raw/SQUAT (PROGRESSION).xlsx'
OUTPUT_JSON_PATH = 'data/processed/exercise_knowledge_base.json'

def run_ingestion():
    print(f"Loading data from {INPUT_EXCEL_PATH}...")
    
    if not os.path.exists(INPUT_EXCEL_PATH):
        print(f"❌ Error: File not found at {INPUT_EXCEL_PATH}")
        return

    try:
        # 1. READ THE MATRIX (The Grid of Exercises)
        df_matrix = pd.read_excel(INPUT_EXCEL_PATH, sheet_name=0, header=2, engine='openpyxl')
        
        # 2. READ THE MANUAL DESCRIPTIONS (New Sheet)
        # We try to read a sheet named 'Descriptions'. If it doesn't exist, we create an empty dict.
        try:
            df_desc = pd.read_excel(INPUT_EXCEL_PATH, sheet_name='Descriptions', engine='openpyxl')
            # Create a lookup dictionary: { "Exercise Name": "Manual Description" }
            desc_lookup = dict(zip(df_desc.iloc[:, 0].str.strip(), df_desc.iloc[:, 1]))
            print("✅ Found 'Descriptions' sheet. Using manual text.")
        except:
            print("⚠️ 'Descriptions' sheet not found. Using generic text.")
            desc_lookup = {}

    except Exception as e:
        print(f"❌ Error reading Excel file: {e}")
        return

    # Clean Matrix Columns
    df_matrix.columns = [str(c).strip() for c in df_matrix.columns]
    df_matrix = df_matrix.dropna(subset=['EXERCISE'])
    
    knowledge_base = []
    count = 0
    
    for _, row in df_matrix.iterrows():
        category = str(row['EXERCISE']).strip()
        
        for level in range(1, 11):
            col_name = f'LEVEL {level}'
            if col_name not in df_matrix.columns: continue
            
            cell_value = row[col_name]
            if pd.isna(cell_value): continue
            
            # Handle multiple exercises in one cell
            exercises = re.split(r',\s*(?![^()]*\))', str(cell_value))
            exercises = [x.strip() for x in exercises if x.strip()]
            
            for ex_name in exercises:
                
                # --- LOGIC: FETCH MANUAL DESCRIPTION ---
                # Check if we have a manual description in the lookup dict
                if ex_name in desc_lookup and pd.notna(desc_lookup[ex_name]):
                    final_description = desc_lookup[ex_name]
                    source = "Manual"
                else:
                    # FALLBACK: If you didn't write one yet, generate a placeholder
                    final_description = (
                        f"A Level {level} {category} exercise. "
                        f"Suitable for FMS corrective strategies focusing on {category.lower()}."
                    )
                    source = "Auto"

                entry = {
                    "id": f"sq_{level}_{count}",
                    "exercise_name": ex_name,
                    "category": category,
                    "difficulty_level": level,
                    "description": final_description, # <--- THIS IS WHAT RAG READS
                    "description_source": source,
                    "tags": [category.lower(), f"level {level}"]
                }
                
                knowledge_base.append(entry)
                count += 1

    # Save to JSON
    os.makedirs(os.path.dirname(OUTPUT_JSON_PATH), exist_ok=True)
    with open(OUTPUT_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(knowledge_base, f, indent=4)
        
    print(f"✅ Success! Processed {count} exercises.")
    print(f"📁 Saved to: {OUTPUT_JSON_PATH}")

if __name__ == "__main__":
    run_ingestion()