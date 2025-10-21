import pdfplumber
import re
import json
import random

PDF_PATH = "Human Computer Interaction W Final.pdf"
OUT_JSON = "questions.json"

# Simple fallback MCQ generator for each module
def extract_modules(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        text = "\n".join(p.extract_text() or "" for p in pdf.pages)

    # Split by module headings
    parts = re.split(r'(Module\s*[-–]\s*[IVXLC]+[:\s].+)', text, flags=re.I)
    modules = {}
    for i in range(1, len(parts), 2):
        title = parts[i].strip()
        content = parts[i+1].strip()
        modules[title] = content
    return modules

def make_fake_mcqs(text, count=5):
    # Very simple generator — looks for sentences and makes concept-based questions
    sentences = [s.strip() for s in re.split(r'[\.\n]', text) if len(s.split()) > 5]
    random.shuffle(sentences)
    questions = []
    for i in range(min(count, len(sentences))):
        base = sentences[i]
        question = f"What best describes this concept: {base[:80]}..."
        options = [
            base.split()[0],
            base.split()[-1],
            "All of the above",
            "None of the above"
        ]
        correct = random.choice(["A", "B", "C", "D"])
        questions.append({
            "question": question,
            "options": options,
            "answer": correct
        })
    return questions

if __name__ == "__main__":
    modules = extract_modules(PDF_PATH)
    result = {}
    for mod, content in modules.items():
        print(f"Generating questions for {mod} ...")
        result[mod] = make_fake_mcqs(content, count=10)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    print(f"✅ Generated new MCQs and saved to {OUT_JSON}")
