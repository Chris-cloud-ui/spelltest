import streamlit as st
import yaml
import json
import os
from datetime import datetime
import random
from gtts import gTTS
import pyphen
import io
import tempfile


# -----------------------------------------------------
# PAGE CONFIG
# -----------------------------------------------------
st.set_page_config(
    page_title="Slay Spells",
    page_icon="🧙‍♀️",
    layout="centered",
    initial_sidebar_state="expanded"
)


# -----------------------------------------------------
# LOAD WORD LISTS
# -----------------------------------------------------
with open("words.yaml", "r") as f:
    WORD_LISTS = yaml.safe_load(f)


# -----------------------------------------------------
# HISTORY FILE
# -----------------------------------------------------
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


# -----------------------------------------------------
# SIDEBAR SETTINGS
# -----------------------------------------------------
st.sidebar.title("⚙️ Settings")

list_choice = st.sidebar.selectbox(
    "Choose a word list:",
    list(WORD_LISTS.keys())
)

shuffle_words = st.sidebar.checkbox("Shuffle words", value=True)

st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Test"):
    st.session_state.clear()
    st.rerun()


# -----------------------------------------------------
# SESSION STATE INIT
# -----------------------------------------------------
if "index" not in st.session_state:
    st.session_state.index = 0
if "score" not in st.session_state:
    st.session_state.score = 0
if "done" not in st.session_state:
    st.session_state.done = False
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "user_word" not in st.session_state:
    st.session_state.user_word = ""


# Load & shuffle words only once
if "words" not in st.session_state:
    words = WORD_LISTS[list_choice][:]
    if shuffle_words:
        random.shuffle(words)
    st.session_state.words = words


# -----------------------------------------------------
# HEADER
# -----------------------------------------------------
st.markdown("""
    <h1 style='text-align:center; color:#ff66a6;'>🧙‍♀️ Slay Spells</h1>
    <p style='text-align:center; font-size:20px; color:#555;'>Practise your spells</p>
""", unsafe_allow_html=True)


# -----------------------------------------------------
# MAIN GAME LOGIC
# -----------------------------------------------------
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
    # CURRENT WORD
    word_info = st.session_state.words[st.session_state.index]
    current_word = word_info["word"]

    st.markdown("### 🔊 Listen and spell the word:")

    # ----------------------------------------
    # Generate Audio (No pydub required)
    # ----------------------------------------
    dic = pyphen.Pyphen(lang='en')
    syllables = word_info.get("syll", dic.inserted(current_word).split("-"))

    # Convert text → mp3 bytes
    def tts_mp3(text, slow=False):
        fp = io.BytesIO()
        gTTS(text=text, lang="en", tld="co.uk", slow=slow).write_to_fp(fp)
        fp.seek(0)
        return fp.read()

    audio_bytes = b""
    audio_bytes += tts_mp3(f"Can you spell {current_word}? ", slow=False)

    if len(syllables) > 1:
        for s in syllables:
            audio_bytes += tts_mp3(s, slow=True)

    # Write out final mp3 file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(audio_bytes)
        audio_filename = tmp.name

    st.audio(audio_filename)

    # Initialize reset flag
    if "reset_input" not in st.session_state:
        st.session_state.reset_input = False
        
    # -----------------------------------------------------
    # SPELLING INPUT FORM
    # -----------------------------------------------------
    with st.form("spell_form"):
        user_input = st.text_input(
            "Type the word:",
            value="" if st.session_state.reset_input else st.session_state.get("user_word", ""),
            key="user_word",
            placeholder="Type here",
            autocomplete="off"
        )
        pressed = st.form_submit_button("Submit")

    # -----------------------------------------------------
    # FORM BUTTON LOGIC
    # -----------------------------------------------------
    if pressed:
        current_word = st.session_state.words[st.session_state.index]["word"]
        
        # Check spelling
        if user_input.upper() == current_word.upper():
            st.success("🌟 Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Not quite. It was **{current_word}**.")
    
        # Clear text box
        #st.session_state["user_word"] = ""
    
        # Move to next word
        st.session_state.index += 1
        if st.session_state.index >= len(st.session_state.words):
            st.session_state.done = True
    
        # Trigger input reset for next render
        st.session_state.reset_input = True
    
        # Refresh app
        st.experimental_rerun()
    else:
        # Ensure value persists while typing
        st.session_state.reset_input = False


# -----------------------------------------------------
# HISTORY PANEL
# -----------------------------------------------------
st.markdown("---")
st.subheader("📊 Past Results")

if not history:
    st.info("No history yet. Complete a test to see stats!")
else:
    for entry in reversed(history[-10:]):
        st.markdown(f"""
            🗓 **{entry['date']}**  
            📚 List: *{entry['list']}*  
            ⭐ Score: **{entry['score']} / {entry['total']}**
            <br><br>
        """, unsafe_allow_html=True)



