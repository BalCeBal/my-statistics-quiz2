import streamlit as st
import pandas as pd
import random
import time
import os
import sys

# --- Configurations ---
PASSWORD = "letmein"
TIMEOUT_SECONDS = 300
QUESTION_TIMER = 60  # seconds
LEADERBOARD_FILE = "leaderboard.csv"

# --- Session Timeout Handling ---
now = time.time()
if "last_active" in st.session_state:
    if now - st.session_state.last_active > TIMEOUT_SECONDS:
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
st.session_state.last_active = now

# --- Styling ---
st.set_page_config(page_title="Statistics Quiz App", page_icon="📊", layout="wide")
st.markdown("""
    <style>
        .main { background-color: #f0f2f6; }
        .stButton>button { font-size: 16px; padding: 8px 24px; margin: 4px 0; }
        .stMarkdown { font-size: 18px; }
    </style>
""", unsafe_allow_html=True)

# --- Password Protection ---
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    password_input = st.text_input("Enter password to access the quiz", type="password")
    if password_input == PASSWORD:
        st.session_state.authenticated = True
        st.rerun()
    else:
        st.stop()

# --- Get Username ---
if "username" not in st.session_state:
    username = st.text_input("Enter your name to begin:")
    if username:
        st.session_state.username = username
        st.session_state.quiz_start_time = time.time()
        st.rerun()
    else:
        st.stop()

# --- Load Quiz Data ---
df = pd.read_csv("all_statistics_quiz_questions.csv")
questions = df.to_dict(orient="records")

# --- Learn Mode Toggle Buttons ---
colA, colB = st.columns([1, 4])
with colA:
    if st.session_state.get("learn_mode", False):
        if st.button("🔙 Back to Quiz"):
            st.session_state.learn_mode = False
            st.rerun()
    else:
        if st.button("📘 Learn"):
            st.session_state.learn_mode = True
            st.rerun()

# --- Learn Mode View ---
if st.session_state.get("learn_mode", False):
    st.title("📘 Learn Mode - Review True Statements")
    for _, row in df.iterrows():
        st.markdown(f"""
        ---
        **Concept:** {row['concept']}  
        **True Statement:** {row['true_statement']}  
        **Justification:** {row['justification']}
        """)

    st.markdown("""
        <br>
        <hr style='border-top: 3px solid #bbb;'>
    """, unsafe_allow_html=True)

    if st.button("🔙 Back to Quiz", key="bottom-back"):
        st.session_state.learn_mode = False
        st.rerun()
    st.stop()

# --- Initialize session state ---
if "index" not in st.session_state:
    st.session_state.index = 0
    st.session_state.score = 0
    st.session_state.answered = False
    st.session_state.total = len(questions)
    st.session_state.correct_answer = None
    st.session_state.justification = ""
    st.session_state.current_question = None
    st.session_state.shuffled_options = None
    st.session_state.timer_start = time.time()
    st.session_state.timer_expired = False
    st.session_state.quiz_finished = False

# --- Display Quiz ---
if st.session_state.index >= st.session_state.total:
    total_time = int(time.time() - st.session_state.quiz_start_time)
    st.success(f"🎉 Quiz finished! {st.session_state.username}, your final score: {st.session_state.score}/{st.session_state.total} in {total_time} seconds")

    if not st.session_state.quiz_finished:
        leaderboard_entry = pd.DataFrame([{
            "username": st.session_state.username,
            "score": st.session_state.score,
            "total": st.session_state.total,
            "time_taken": total_time
        }])
        if os.path.exists(LEADERBOARD_FILE):
            existing = pd.read_csv(LEADERBOARD_FILE)
            updated = pd.concat([existing, leaderboard_entry], ignore_index=True)
            updated.to_csv(LEADERBOARD_FILE, index=False)
        else:
            leaderboard_entry.to_csv(LEADERBOARD_FILE, index=False)
        st.session_state.quiz_finished = True

    if st.button("🔄 Restart Quiz"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

else:
    if st.session_state.current_question is None:
        question = questions[st.session_state.index]
        options = [(question["true_statement"], True), (question["false_statement"], False)]
        random.shuffle(options)
        st.session_state.current_question = question
        st.session_state.shuffled_options = options
        st.session_state.answered = False
        st.session_state.correct_answer = None
        st.session_state.justification = ""
        st.session_state.timer_start = time.time()
        st.session_state.timer_expired = False

    st.title("📊 Statistics True/False Quiz")
    st.markdown(f"**User:** {st.session_state.username}")
    st.markdown(f"**Question {st.session_state.index + 1} of {st.session_state.total}**")
    st.markdown(f"**Concept:** {st.session_state.current_question['concept']}")
    st.markdown("⏳ You have up to **60 seconds** to answer each question.")

    # --- Answer Buttons ---
    opt1, opt2 = st.session_state.shuffled_options

    if not st.session_state.answered:
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Select: " + opt1[0]):
                st.session_state.answered = True
                st.session_state.correct_answer = opt1[1]
                st.session_state.justification = st.session_state.current_question["justification"]
                if opt1[1]:
                    st.session_state.score += 1
                st.rerun()
        with col2:
            if st.button("Select: " + opt2[0]):
                st.session_state.answered = True
                st.session_state.correct_answer = opt2[1]
                st.session_state.justification = st.session_state.current_question["justification"]
                if opt2[1]:
                    st.session_state.score += 1
                st.rerun()
    elif st.session_state.answered:
        if st.session_state.correct_answer:
            st.success("✅ Correct!")
        else:
            st.error("❌ Incorrect.")
        st.markdown(f"**Justification:** {st.session_state.justification}")

        if st.button("Next Question"):
            st.session_state.index += 1
            st.session_state.current_question = None
            st.session_state.shuffled_options = None
            st.rerun()

# --- Sidebar Score and Leaderboard ---
st.sidebar.title("📈 Score")
st.sidebar.markdown(f"User: **{st.session_state.username}**")
st.sidebar.markdown(f"Current score: **{st.session_state.score}** / {st.session_state.total}")
st.sidebar.markdown(f"Questions left: **{st.session_state.total - st.session_state.index - (1 if st.session_state.answered else 0)}**")

if os.path.exists(LEADERBOARD_FILE):
    lb = pd.read_csv(LEADERBOARD_FILE)
    if 'time_taken' in lb.columns:
        lb = lb.sort_values(by=["score", "time_taken"], ascending=[False, True])
    else:
        lb = lb.sort_values(by="score", ascending=False)
    st.sidebar.markdown("### 🏆 Leaderboard (Top 10)")
    lb_display = lb[["username", "score", "total", "time_taken"]].head(10).reset_index(drop=True)
    lb_display.index += 1  # Start leaderboard from 1
    st.sidebar.dataframe(lb_display)

# --- Exit Button Always in Sidebar ---
if st.sidebar.button("❌ Exit Quiz"):
    for key in list(st.session_state.keys()):
        del st.session_state[key]
    st.sidebar.write("✅ You can now close this tab. The app is stopped for your session.")
    st.stop()
