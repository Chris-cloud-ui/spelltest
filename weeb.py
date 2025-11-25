import streamlit as st
import yaml
import json
import os
from datetime import datetime
import random
from gtts import gTTS
import io
import tempfile

st.set_page_config(
    page_title="Slay Spells",
    page_icon="🧙‍♀️",
    layout="centered",
    initial_sidebar_state="expanded"
)

# ------------------ LOAD WORDS ------------------
with open("words.yaml", "r") as f:
    WORD_LISTS = yaml.safe_load(f)

# ------------------ HISTORY ---------------------
HISTORY_FILE = "history.json"
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

with open(HISTORY_FILE, "r") as f:
    history = json.load(f)

def save_history(entry):
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# ------------------ SIDEBAR ----------------------
st.sidebar.title("⚙️ Settings")
list_choice = st.sidebar.selectbox(
    "Choose a word list:",
    list(WORD_LISTS.keys())
)

shuffle = st.sidebar.checkbox("Shuffle words", value=True)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Test"):
    st.session_state.clear()
    st.rerun()

# ------------------ SESSION STATE INIT ------------------
if "index" not in st.session_state:
    st.session_state.index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "done" not in st.session_state:
    st.session_state.done = False
if "words" not in st.session_state:
    words = WORD_LISTS[list_choice][:]
    if shuffle:
        random.shuffle(words)
    st.session_state.words = words
if "text_submitted" not in st.session_state:
    st.session_state.text_submitted = False
if "mc_submitted" not in st.session_state:
    st.session_state.mc_submitted = False
if "mode" not in st.session_state:
    st.session_state.mode = None  # "text" or "mc"

# ------------------ HEADER ------------------------
st.markdown("""
<h1 style='text-align:center; color:#ff66a6;'>
    🧙‍♀️ Slay Spells
</h1>
<p style='text-align:center; font-size:20px; color:#555;'>
    Practise your spells
</p>
""", unsafe_allow_html=True)

# ------------------ MAIN APP ----------------------
if st.session_state.done:
    total = len(st.session_state.words)
    score = st.session_state.score

    st.success(f"🎉 All done! You scored **{score} / {total}**")

    # Save to history
    save_history({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "list": list_choice,
        "score": score,
        "total": total
    })
    st.balloons()

else:
    current_word_details = st.session_state.words[st.session_state.index]
    current_word = current_word_details["word"]

    # Randomly decide input mode if not already set
    if st.session_state.mode is None:
        if "spell" in current_word_details and random.choice([True, False]):
            st.session_state.mode = "mc"
        else:
            st.session_state.mode = "text"

    if st.session_state.mode == "text":
        st.markdown(f"### 🔊 Listen and spell the word:")

        # Generate audio
        def tts_bytes(text):
            fp = io.BytesIO()
            gTTS(text=text, lang="en", tld="co.uk", slow=False).write_to_fp(fp)
            fp.seek(0)
            return fp.read()

        audio_bytes = tts_bytes(f"Can you spell {current_word}?")
        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(audio_bytes)
            temp_filename = tmp.name

        st.audio(temp_filename)

        # Text input form
        with st.form(key=f"text_form_{st.session_state.index}"):
            user_word = st.text_input(
                "Type the word:",
                value="",  
                placeholder="Type here",
                autocomplete="off"
            )
            button_label = "Next Word" if st.session_state.text_submitted else "Submit"
            submitted = st.form_submit_button(button_label)

        if submitted:
            if not st.session_state.text_submitted:
                # First click → check answer
                if user_word.upper() == current_word.upper():
                    st.success("🌟 Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Not quite. It was **{current_word}**.")
                st.session_state.text_submitted = True
            else:
                # Second click → next word
                st.session_state.index += 1
                st.session_state.text_submitted = False
                st.session_state.mode = None
                st.rerun()

    else:  # multiple choice mode
        st.markdown("### ❓ Choose the correct spelling:")

        options = [current_word] + current_word_details["spell"]
        random.shuffle(options)

        # Track which button has been clicked
        if "mc_clicked" not in st.session_state:
            st.session_state.mc_clicked = None

        def mc_click(option):
            st.session_state.mc_clicked = option
            if option == current_word:
                st.session_state.mc_submitted = "correct"
                st.session_state.score += 1
            else:
                st.session_state.mc_submitted = "wrong"

        # Display buttons
        for opt in options:
            color = "#1E90FF"  # blue default
            icon = ""
            if st.session_state.mc_clicked == opt:
                if st.session_state.mc_submitted == "correct":
                    color = "#28a745"  # green
                    icon = " ✅"
                elif st.session_state.mc_submitted == "wrong":
                    color = "#dc3545"  # red
                    icon = " ❌"
            st.markdown(
                f"""
                <style>
                .button-{opt} {{
                    display: block;
                    width: 100%;
                    background-color: {color};
                    color: white;
                    border: none;
                    padding: 10px;
                    font-size: 18px;
                    margin-bottom:5px;
                    text-align:center;
                    border-radius:5px;
                }}
                </style>
                <form action="" method="post">
                <button class="button-{opt}" name="btn" value="{opt}">{opt}{icon}</button>
                </form>
                """,
                unsafe_allow_html=True
            )

        # Next word button after submission
        if st.session_state.mc_submitted:
            if st.button("Next Word"):
                st.session_state.index += 1
                st.session_state.mode = None
                st.session_state.mc_submitted = False
                st.session_state.mc_clicked = None
                st.rerun()

# ------------------ HISTORY PANEL ----------------------
st.markdown("---")
st.subheader("📊 Past Results")
if len(history) == 0:
    st.info("No history yet. Complete a test to see stats!")
else:
    for entry in reversed(history[-10:]):
        st.markdown(f"""
            🗓 **{entry['date']}**  
            📚 List: *{entry['list']}*  
            ⭐ Score: **{entry['score']} / {entry['total']}**
            <br><br>
        """, unsafe_allow_html=True)


