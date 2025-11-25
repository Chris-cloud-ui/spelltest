import streamlit as st
import yaml
import json
import os
import random
from datetime import datetime
from gtts import gTTS
import io
import tempfile

st.set_page_config(page_title="Slay Spells", page_icon="🧙‍♀️", layout="centered")

# Load words
with open("words.yaml") as f:
    WORD_LISTS = yaml.safe_load(f)

HISTORY_FILE = "history.json"
if not os.path.exists(HISTORY_FILE):
    with open(HISTORY_FILE, "w") as f:
        json.dump([], f)

with open(HISTORY_FILE) as f:
    history = json.load(f)

def save_history(entry):
    history.append(entry)
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)

# Sidebar
st.sidebar.title("⚙️ Settings")
list_choice = st.sidebar.selectbox("Choose a word list:", list(WORD_LISTS.keys()))
shuffle = st.sidebar.checkbox("Shuffle words", value=True)
if st.sidebar.button("🔄 Reset Test"):
    st.session_state.clear()
    st.rerun()

# Session state
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
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "mc_done" not in st.session_state:
    st.session_state.mc_done = False

# Header
st.markdown("""
<h1 style='text-align:center; color:#ff66a6;'>🧙‍♀️ Slay Spells</h1>
<p style='text-align:center; font-size:20px; color:#555;'>Practise your spells</p>
""", unsafe_allow_html=True)

# Done?
if st.session_state.done:
    total = len(st.session_state.words)
    score = st.session_state.score
    st.success(f"🎉 All done! You scored **{score} / {total}**")
    save_history({
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
        "list": list_choice,
        "score": score,
        "total": total
    })
    st.balloons()
else:
    word_data = st.session_state.words[st.session_state.index]
    current_word = word_data["word"]

    # Decide quiz type
    use_mc = "spell" in word_data and random.choice([True, False])

    if not use_mc:
        # Text input quiz with audio
        st.markdown("### 🔊 Listen and spell the word:")

        # Generate audio
        def tts_bytes(text, slow=False):
            fp = io.BytesIO()
            tts = gTTS(text=text, lang="en", tld="co.uk", slow=slow)
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()

        final_audio = tts_bytes(f"Can you spell {current_word}?")
        if "syll" in word_data:
            for s in word_data["syll"]:
                final_audio += tts_bytes(s, slow=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(final_audio)
            temp_file = tmp.name
        st.audio(temp_file)

        # Text input form
        with st.form("text_form"):
            user_word = st.text_input("Type the word:", key="user_word", placeholder="Type here", autocomplete="off")
            button_label = "Next Word" if st.session_state.submitted else "Submit"
            submitted = st.form_submit_button(button_label)

        if submitted:
            if not st.session_state.submitted:
                # First click = check
                if user_word.upper() == current_word.upper():
                    st.success("✅ Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Not quite. Correct: {current_word}")
                st.session_state.submitted = True
            else:
                # Next word
                st.session_state.user_word = ""  # text cleared automatically on rerun
                st.session_state.submitted = False
                st.session_state.index += 1
                if st.session_state.index >= len(st.session_state.words):
                    st.session_state.done = True
                st.rerun()
    else:
        # Multiple choice
        st.markdown("### ❓ Choose the correct spelling:")
        choices = [current_word] + word_data["spell"]
        random.shuffle(choices)

        if "mc_choice" not in st.session_state:
            st.session_state.mc_choice = None

        # Use HTML buttons for styling
        buttons_html = "<div style='display:flex; flex-direction:column; gap:10px;'>"
        for i, opt in enumerate(choices):
            color = "#007bff"
            if st.session_state.mc_done:
                if opt == current_word:
                    color = "green"
                elif st.session_state.mc_choice == opt:
                    color = "red"
            buttons_html += f"""
            <form action=''>
                <input type='submit' value='{opt}' style='background-color:{color}; color:white; font-size:20px; width:100%; padding:10px;' onclick="fetch('/?mc_choice={opt}', {{method:'POST'}})">
            </form>
            """
        buttons_html += "</div>"
        st.markdown(buttons_html, unsafe_allow_html=True)

        # Check if choice made via session_state
        if st.session_state.mc_done:
            if st.session_state.mc_choice == current_word:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error(f"❌ Not quite. Correct: {current_word}")

            if st.button("Next Word"):
                st.session_state.mc_done = False
                st.session_state.mc_choice = None
                st.session_state.index += 1
                if st.session_state.index >= len(st.session_state.words):
                    st.session_state.done = True
                st.rerun()
