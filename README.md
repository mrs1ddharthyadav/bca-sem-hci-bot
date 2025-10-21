# 🎓 Telegram Quiz Bot (Auto-Module Learning System)

A fully automated **Telegram quiz bot** built with Python and the `python-telegram-bot` library.  
It fetches multiple-choice questions from a JSON file (`questions.json`) and presents them to users as **interactive quiz polls** — one question at a time — until the entire module is completed.

After each question, the bot provides instant feedback, keeps track of the user’s score, and automatically moves to the next question.  
Once a module is completed, it shows the final score and asks if the user wants to continue with the next module.

---

## 🚀 Features

- ✅ **Interactive Telegram Polls** — Uses Telegram’s quiz-type polls with automatic correctness checking.
- 🧠 **Modular Question System** — Loads questions dynamically from `questions.json`.
- 🔄 **Automatic Progression** — Continues to the next question after answering (no manual restart).
- 🏁 **Completion Summary** — Displays total correct answers and performance at the end of each module.
- 💾 **SQLite Database Support** — Saves user progress and scores.
- 📊 **Answer Explanations** — Provides instant feedback and explanations for correct answers.
- 🧩 **Multiple Modules Support** — Handles multiple sets of questions (Module 1, Module 2, etc.).
- 🔐 **User State Tracking** — Remembers each user’s current question index and module.

---

## 🧰 Tech Stack

| Component | Description |
|------------|-------------|
| **Language** | Python 3.10+ |
| **Framework** | [python-telegram-bot v20+](https://docs.python-telegram-bot.org/) |
| **Database** | SQLite3 |
| **Data Format** | JSON (`questions.json`) |
| **Logging** | Built-in Python `logging` for error & event tracking |

---

## 📁 Project Structure

