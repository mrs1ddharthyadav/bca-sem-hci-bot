# parse_pdf.py
import pdfplumber
import re
import json
from collections import defaultdict

PDF_PATH = "Human Computer Interaction W Final.pdf"
OUT_JSON = "questions.json"

def extract_text_by_page(pdf_path):
    pages = []
    with pdfplumber.open(pdf_path) as pdf:
        for p in pdf.pages:
            pages.append(p.extract_text() or "")
    return pages

def find_modules(text):
    # Heuristic: lines starting with "Module - I:" or "Module - I" etc.
    module_re = re.compile(r'^(Module\s*[-–]\s*[IVXLC]+[:\s].+)$', re.IGNORECASE | re.M)
    modules = []
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = module_re.search(ln.strip())
        if m:
            modules.append((i, ln.strip()))
    return modules

def parse_mcqs_from_text(text):
    # Heuristic parsing: look for patterns like "1." / "Q1." or "Q 1." then A., B., C., D. and Answer:
    questions = []
    # split into potential blocks
    blocks = re.split(r'\n\s*\n', text)
    for b in blocks:
        # find a question number at start
        if re.search(r'^\s*(Q\s*\d+|Question\s*\d+|\d+\.)', b, re.IGNORECASE):
            # try extract options A-D
            opts = re.findall(r'(?:\n|^)\s*([A-D])[\.\)]\s*(.+?)(?=(?:\n\s*[A-D][\.\)]\s)|\n\s*Answer:|\Z)', b, flags=re.S|re.I)
            if opts and len(opts) >= 2:
                opts_sorted = [None]*len(opts)
                for o in opts:
                    idx = ord(o[0].upper()) - ord('A')
                    if 0 <= idx < 10:
                        opts_sorted[idx] = o[1].strip().replace('\n',' ')
                # get answer
                ans_m = re.search(r'Answer[:\s]*([A-D]|[abcd]|[A-D]\))', b, re.I)
                ans = None
                if ans_m:
                    ans = ans_m.group(1).strip().upper().replace(')','').replace('.','')
                # question text (first line)
                qtext = re.split(r'\n', b, maxsplit=1)[0].strip()
                # sanity: require 2+ options and answer not None
                if any(opts_sorted) and ans:
                    # fill missing options as "N/A"
                    opts_clean = [o if o else "N/A" for o in opts_sorted]
                    questions.append({
                        "question": re.sub(r'^(Q\s*\d+|Question\s*\d+|\d+\.)\s*', '', qtext, flags=re.I),
                        "options": opts_clean,
                        "answer": ans
                    })
    return questions

def build_by_module(pdf_path):
    pages = extract_text_by_page(pdf_path)
    full_text = "\n\n".join(pages)
    # crude: split by "Module - " headings
    module_splits = re.split(r'(Module\s*[-–]\s*[IVXLC]+[:\s].+)', full_text, flags=re.I)
    # module_splits will be like ['', 'Module - I: ...', 'text', 'Module - II: ...', 'text' ...]
    modules = {}
    if len(module_splits) <= 1:
        # fallback: whole document as Module 1
        modules["Module 1"] = parse_mcqs_from_text(full_text)
        return modules

    for i in range(1, len(module_splits), 2):
        title = module_splits[i].strip()
        content = module_splits[i+1]
        qlist = parse_mcqs_from_text(content)
        modules[title] = qlist

    return modules

if __name__ == "__main__":
    modules = build_by_module(PDF_PATH)
    # save
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(modules, f, indent=2, ensure_ascii=False)
    print(f"Saved questions to {OUT_JSON}. Review and add generated questions if needed.")
