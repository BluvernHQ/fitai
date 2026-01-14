import torch
from transformers import DistilBertTokenizer, DistilBertForSequenceClassification

# Load your custom trained model
MODEL_PATH = "./models/fms_bert_finetuned"

print("⏳ Loading Model...")
tokenizer = DistilBertTokenizer.from_pretrained(MODEL_PATH)
model = DistilBertForSequenceClassification.from_pretrained(MODEL_PATH)
model.eval() # Set to evaluation mode

# MAPPING (ID -> Meaning)
LABELS = {
    0: "🔴 STOP (Medical)",
    1: "🟢 MOBILITY (Level 1)",
    2: "🟡 STABILITY (Level 3)",
    3: "🔴 PATTERN (Level 5)",
    4: "🔴 STRENGTH (Level 7)",
    5: "🔴 POWER (Level 9)"
}

def predict_level(scores):
    # 1. Format Input exactly like training
    text_input = (
        f"Deep Squat: {scores[0]}, Hurdle Step: {scores[1]}, Inline Lunge: {scores[2]}, "
        f"Shoulder Mobility: {scores[3]}, ASLR: {scores[4]}, "
        f"Trunk Stability: {scores[5]}, Rotary Stability: {scores[6]}"
    )
    
    # 2. Tokenize
    inputs = tokenizer(text_input, return_tensors="pt", truncation=True, max_length=64)
    
    # 3. Predict
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 4. Get Result
    prediction_id = torch.argmax(outputs.logits, dim=1).item()
    confidence = torch.softmax(outputs.logits, dim=1)[0][prediction_id].item()
    
    return LABELS[prediction_id], confidence

# TEST CASES
print("\n--- 🤖 AI DIAGNOSIS ---")

# Case A: Perfect Athlete (All 3s)
print(f"Input: All 3s (Perfect) -> {predict_level([3,3,3,3,3,3,3])}")

# Case B: Bad Mobility (Shoulder = 1)
print(f"Input: Shoulder=1 (Stiff) -> {predict_level([3,3,3,1,3,3,3])}")

# Case C: Pain (Score 0)
print(f"Input: Pain Present (0)  -> {predict_level([2,2,2,2,0,2,2])}")