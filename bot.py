import os
import json
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, PollAnswer
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler,
    PollAnswerHandler,
)
from dotenv import load_dotenv

load_dotenv()
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
QUESTION_FILE = os.getenv("QUESTION_FILE", "questions.json")
DB_FILE = os.getenv("DB_FILE", "quiz_scores.db")
QUESTION_TIMER = 10  # seconds

# Load questions
try:
    with open(QUESTION_FILE, "r", encoding="utf-8") as f:
        QUESTIONS_BY_MODULE = json.load(f)
except FileNotFoundError:
    logger.error(f"Question file '{QUESTION_FILE}' not found. Please run parse_pdf.py first.")
    QUESTIONS_BY_MODULE = {}

MODULE_TITLES = list(QUESTIONS_BY_MODULE.keys())

# Database setup
def init_db():
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS user_scores (
            user_id INTEGER,
            module TEXT,
            score INTEGER DEFAULT 0,
            total INTEGER DEFAULT 0,
            PRIMARY KEY (user_id, module)
        )
    """)
    conn.commit()
    conn.close()

def update_score(user_id, module, correct):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO user_scores (user_id, module, score, total) VALUES (?, ?, 0, 0)", (user_id, module))
    if correct:
        c.execute("UPDATE user_scores SET score = score + 1, total = total + 1 WHERE user_id=? AND module=?", (user_id, module))
    else:
        c.execute("UPDATE user_scores SET total = total + 1 WHERE user_id=? AND module=?", (user_id, module))
    conn.commit()
    conn.close()

def get_score(user_id, module):
    conn = sqlite3.connect(DB_FILE)
    c = conn.cursor()
    c.execute("SELECT score, total FROM user_scores WHERE user_id=? AND module=?", (user_id, module))
    row = c.fetchone()
    conn.close()
    return row if row else (0, 0)

# Explanation logic
def generate_explanation(question, answer_text, custom_explanation=None):
    if custom_explanation and custom_explanation.strip():
        return custom_explanation
    if "interaction" in question.lower():
        return "It focuses on how users engage with computer systems effectively."
    elif "design" in question.lower():
        return "Design in HCI ensures usability and better user experience."
    else:
        return f"The correct answer '{answer_text}' fits best based on the core HCI concepts."

# /start command
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message: return
    keyboard = [[InlineKeyboardButton(text=m, callback_data=m)] for m in MODULE_TITLES]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(
        "👋 Welcome to the *HCI Quiz Bot!*\n\nChoose a module to begin:",
        parse_mode="Markdown",
        reply_markup=reply_markup
    )

# Module selection
async def choose_module(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    module = query.data

    if module not in QUESTIONS_BY_MODULE:
        await query.edit_message_text("❌ Module not found. Please try again.")
        return

    context.user_data["module"] = module
    context.user_data["q_index"] = 0

    await query.edit_message_text(
        f"✅ You selected *{module}*\n\nGet ready for your quiz!",
        parse_mode="Markdown"
    )

    # Start the quiz
    await send_next_poll_by_chat_id(context, query.from_user.id)

# Send poll (track poll_id)
async def send_next_poll_by_chat_id(context: ContextTypes.DEFAULT_TYPE, chat_id: int):
    module = context.user_data.get("module")
    q_index = context.user_data.get("q_index", 0)
    qlist = QUESTIONS_BY_MODULE.get(module, [])

    if q_index >= len(qlist):
        # Quiz completed
        score, total = get_score(chat_id, module)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🎉 Quiz completed for *{module}*!\n✅ You got {score}/{total} correct.",
            parse_mode="Markdown"
        )
        context.user_data.pop("module", None)
        context.user_data.pop("q_index", None)
        return

    q = qlist[q_index]
    question = q.get("question", "No question")
    options = q.get("options", [])
    correct_answer_value = q.get("answer", options[0]).strip().lower()

    # Determine correct option index
    correct_index = 0
    for i, opt in enumerate(options):
        if correct_answer_value == opt.strip().lower():
            correct_index = i
            break

    # Send quiz poll
    poll_message = await context.bot.send_poll(
        chat_id=chat_id,
        question=f"Q{q_index+1}. {question}",
        options=options,
        type="quiz",
        correct_option_id=correct_index,
        is_anonymous=False,
    )

    # Store mapping of poll_id → question_index
    if "polls" not in context.user_data:
        context.user_data["polls"] = {}
    context.user_data["polls"][poll_message.poll.id] = q_index


async def handle_poll_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    poll_answer = update.poll_answer
    user_id = poll_answer.user.id
    poll_id = poll_answer.poll_id

    if "polls" not in context.user_data or poll_id not in context.user_data["polls"]:
        return  # Unknown poll

    q_index = context.user_data["polls"][poll_id]
    module = context.user_data.get("module")
    q = QUESTIONS_BY_MODULE[module][q_index]
    options = q.get("options", [])
    correct_answer_value = q.get("answer", options[0]).strip().lower()

    # Determine correct index
    correct_index = 0
    for i, opt in enumerate(options):
        if correct_answer_value == opt.strip().lower():
            correct_index = i
            break

    user_choice = poll_answer.option_ids[0] if poll_answer.option_ids else None
    is_correct = (user_choice == correct_index)

    # Update score
    update_score(user_id, module, is_correct)

    # Send explanation
    correct_answer_text = options[correct_index]
    explanation = generate_explanation(q["question"], correct_answer_text, q.get("explanation"))
    await context.bot.send_message(
        chat_id=user_id,
        text=f"✅ Correct answer: *{correct_answer_text}*\n💡 {explanation}",
        parse_mode="Markdown"
    )

    # Move to next question
    context.user_data["q_index"] = q_index + 1
    await send_next_poll_by_chat_id(context, user_id)

# MAIN
def main():
    init_db()
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set. Check your .env file.")
        return

    app = Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(choose_module))
    app.add_handler(PollAnswerHandler(handle_poll_answer))

    logger.info("Bot polling...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
