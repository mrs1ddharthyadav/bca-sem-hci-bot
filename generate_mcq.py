# generate_mcq.py
import os, json
from dotenv import load_dotenv
load_dotenv()
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")
IN_JSON = "questions.json"
OUT_JSON = "questions_augmented.json"
MAX_PER_MODULE = 10

def generate_mcqs_for_module(module_title, module_text, count=5):
    prompt = f"""You are an exam question writer. Make {count} multiple choice questions (4 options A-D) on this topic. Provide correct answer letter. Keep questions clear and factual.

Topic: {module_title}

Content:
{module_text}

Return JSON array of objects: {{ "question": "...", "options":["...","...","...","..."], "answer":"A" }}
"""
    resp = openai.ChatCompletion.create(
        model="gpt-4o-mini",  # or a model you have access to; change if needed
        messages=[{"role":"user","content":prompt}],
        temperature=0.2,
        max_tokens=1200
    )
    text = resp.choices[0].message.content
    # We expect JSON; try to parse
    try:
        arr = json.loads(text)
        return arr
    except Exception as e:
        print("OpenAI response not parseable automatically. Returning empty.")
        return []

if __name__ == "__main__":
    # this script assumes you have textual content per module; for simplicity we'll load questions.json for module keys
    with open(IN_JSON, "r", encoding="utf-8") as f:
        data = json.load(f)
    augmented = {}
    for module_title, qlist in data.items():
        # basic stub: generate synthetic Qs using the concatenation of question texts (fallback)
        module_text = " ".join([q['question'] + " " + " ".join(q['options']) for q in qlist])
        print("Generating for", module_title)
        new_qs = generate_mcqs_for_module(module_title, module_text, count=MAX_PER_MODULE)
        augmented[module_title] = qlist + new_qs
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(augmented, f, indent=2, ensure_ascii=False)
    print("Saved augmented questions to", OUT_JSON)
