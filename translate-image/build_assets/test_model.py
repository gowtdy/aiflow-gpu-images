from transformers import AutoModelForCausalLM, AutoTokenizer
import os

model_path = "/app/models/mt_models"

print(f"Loading model from {model_path}")
print(f"Loading tokenizer from {model_path}")
tokenizer = AutoTokenizer.from_pretrained(model_path)
print(f"Loading model from {model_path}")
model = AutoModelForCausalLM.from_pretrained(model_path, device_map="auto")  # You may want to use bfloat16 and/or move to GPU here
print(f"Model loaded")
print(f"Loading messages")
messages = [
    {"role": "user", "content": "Translate the following segment into Chinese, without additional explanation.\n\nIt’s on the house."},
]
tokenized_chat = tokenizer.apply_chat_template(
    messages,
    tokenize=True,
    add_generation_prompt=False,
    return_tensors="pt"
)

outputs = model.generate(tokenized_chat.to(model.device), max_new_tokens=2048)
print(f"Generating outputs: {outputs}")
output_text = tokenizer.decode(outputs[0])
print(f"Output text: {output_text}")