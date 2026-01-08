import pandas as pd
import numpy as np
import torch
import os
from datasets import Dataset
from transformers import (
    DistilBertTokenizer, 
    DistilBertForSequenceClassification, 
    Trainer, 
    TrainingArguments,
    DataCollatorWithPadding
)
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# ==========================================
# CONFIGURATION
# ==========================================
MODEL_NAME = "distilbert-base-uncased"
OUTPUT_DIR = "./models/fms_bert_finetuned"
NUM_SAMPLES = 3000  # Amount of data to "teach" the model
EPOCHS = 3          # How many times to study the data

# ==========================================
# 1. DATA GENERATION (The "Knowledge Distillation")
# ==========================================
def generate_expert_data(n_samples=2000):
    """
    Generates training data by applying YOUR Expert Rules to random scores.
    This teaches the Deep Learning model to mimic your logic perfectly.
    """
    data = []
    labels = []
    
    # MAPPING: Matches your project's logic
    # 0: Medical (Stop)
    # 1: Mobility (Green)
    # 2: Stability (Yellow)
    # 3: Patterning (Level 5)
    # 4: Strength (Level 7)
    # 5: Power (Level 9)
    
    print(f"📊 Generating {n_samples} training examples based on Expert Logic...")
    
    for _ in range(n_samples):
        # Generate Random Scores (Weighted to be realistic)
        # 0 (Pain) is rare (5%), 2 is common (50%)
        profile = np.random.choice([0, 1, 2, 3], size=7, p=[0.05, 0.2, 0.5, 0.25])
        ds, hs, il, sm, aslr, tsp, rs = profile
        
        # --- A. CREATE INPUT TEXT (The "Prompt") ---
        # Transformers read text, so we convert numbers to a sentence.
        # This allows you to add "Patient Notes" later easily.
        text_input = (
            f"Deep Squat: {ds}, Hurdle Step: {hs}, Inline Lunge: {il}, "
            f"Shoulder Mobility: {sm}, ASLR: {aslr}, "
            f"Trunk Stability: {tsp}, Rotary Stability: {rs}"
        )
        
        # --- B. ASSIGN LABEL (The "Answer") ---
        # This matches your 'fms_analyzer.py' logic EXACTLY.
        
        if 0 in profile:
            label = 0 # STOP/Medical
        elif aslr <= 1 or sm <= 1:
            label = 1 # Mobility
        elif tsp <= 1 or rs <= 1:
            label = 2 # Stability
        elif ds == 1:
            label = 3 # Patterning
        elif ds == 2:
            label = 4 # Strength
        else:
            label = 5 # Power
            
        data.append(text_input)
        labels.append(label)

    return pd.DataFrame({'text': data, 'label': labels})

# ==========================================
# 2. METRICS (To measure success)
# ==========================================
def compute_metrics(pred):
    labels = pred.label_ids
    preds = pred.predictions.argmax(-1)
    acc = accuracy_score(labels, preds)
    return {"accuracy": acc}

# ==========================================
# 3. MAIN TRAINING PIPELINE
# ==========================================
def train():
    # --- Step 1: Prepare Data ---
    df = generate_expert_data(NUM_SAMPLES)
    train_df, test_df = train_test_split(df, test_size=0.2, random_state=42)
    
    # Convert to Hugging Face Dataset
    train_dataset = Dataset.from_pandas(train_df)
    test_dataset = Dataset.from_pandas(test_df)
    
    # --- Step 2: Tokenization ---
    print(f"📥 Downloading Pre-trained Model ({MODEL_NAME})...")
    tokenizer = DistilBertTokenizer.from_pretrained(MODEL_NAME)
    
    def tokenize_function(examples):
        return tokenizer(examples["text"], truncation=True, padding="max_length", max_length=64)
    
    tokenized_train = train_dataset.map(tokenize_function, batched=True)
    tokenized_test = test_dataset.map(tokenize_function, batched=True)
    
    # --- Step 3: Load Model ---
    # num_labels=6 because we have 6 distinct levels (0, 1, 2, 3, 4, 5)
    model = DistilBertForSequenceClassification.from_pretrained(MODEL_NAME, num_labels=6)
    
    # --- Step 4: Setup Trainer ---
    training_args = TrainingArguments(
        output_dir="./results",
        eval_strategy="epoch",
        save_strategy="epoch",
        learning_rate=2e-5,           # Very small learning rate for fine-tuning
        per_device_train_batch_size=16,
        per_device_eval_batch_size=16,
        num_train_epochs=EPOCHS,
        weight_decay=0.01,
        logging_dir='./logs',
        load_best_model_at_end=True,  # Saves the version with highest accuracy
    )
    
    data_collator = DataCollatorWithPadding(tokenizer=tokenizer)
    
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_test,
        processing_class=tokenizer,
        data_collator=data_collator,
        compute_metrics=compute_metrics,
    )
    
    # --- Step 5: Train ---
    print("\n🚀 Starting Deep Learning Training (Fine-Tuning)...")
    trainer.train()
    
    # --- Step 6: Final Evaluation ---
    print("\n🧪 Evaluating Final Model...")
    eval_result = trainer.evaluate()
    print(f"✅ Final Accuracy: {eval_result['eval_accuracy']*100:.2f}%")
    
    # --- Step 7: Save ---
    print(f"\n💾 Saving Model to {OUTPUT_DIR}...")
    model.save_pretrained(OUTPUT_DIR)
    tokenizer.save_pretrained(OUTPUT_DIR)
    print("🎉 DONE! Your Deep Learning model is ready.")

if __name__ == "__main__":
    train()