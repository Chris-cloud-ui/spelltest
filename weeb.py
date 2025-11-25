import streamlit as st
import yaml
import json
import os
from datetime import datetime
import random
from gtts import gTTS
import io
import tempfile
import pyphen

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
list_choice = st.sidebar.selectbox("Choose a word list:", list(WORD_LISTS.keys()))
shuffle = st.sidebar.checkbox("Shuffle words", value=True)
st.sidebar.markdown("---")
if st.sidebar.button("🔄 Reset Test"):
    st.session_state.clear()
    st.experimental_rerun()

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

if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "show_next" not in st.session_state:
    st.session_state.show_next = False
if "last_result" not in st.session_state:
    st.session_state.last_result = None
if "mode" not in st.session_state:
    st.session_state.mode = None  # "text" or "mc"

# ------------------ HEADER ------------------------
st.markdown("""
<h1 style='text-align:center; color:#ff66a6;'>🧙‍♀️ Slay Spells</h1>
<p style='text-align:center; font-size:20px; color:#555;'>Practise your spells</p>
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

    # ------------------ MODE SELECTION ------------------
    if st.session_state.mode is None:
        if "spell" in current_word_details and random.random() < 0.5:
            st.session_state.mode = "mc"
        else:
            st.session_state.mode = "text"

    # ------------------ TEXT INPUT MODE ------------------
    if st.session_state.mode == "text":
        st.markdown("### 🔊 Listen and spell the word:")

        # Generate audio
        dic = pyphen.Pyphen(lang='en')
        syllables = dic.inserted(current_word).split('-')
        if "syll" in current_word_details:
            syllables = current_word_details["syll"]

        def tts_bytes(text, slow=False):
            fp = io.BytesIO()
            tts = gTTS(text=text, lang="en", tld="co.uk", slow=slow)
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()

        final_mp3 = b""
        final_mp3 += tts_bytes(f"Can you spell {current_word}?", slow=False)
        if len(syllables) > 1:
            for s in syllables:
                final_mp3 += tts_bytes(s, slow=True)

        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
            tmp.write(final_mp3)
            temp_filename = tmp.name
        st.audio(temp_filename)

        # Text input form
        with st.form(key=f"text_form_{st.session_state.index}"):
            user_word = st.text_input(
                "Type the word:",
                key=f"user_word_{st.session_state.index}",
                placeholder="Type here",
                autocomplete="off",
                disabled=st.session_state.submitted
            )
            button_label = "Next Word" if st.session_state.submitted else "Submit"
            submitted = st.form_submit_button(button_label)

        if submitted and not st.session_state.submitted:
            if user_word.upper() == current_word.upper():
                st.session_state.last_result = f"🌟 Correct!"
                st.session_state.score += 1
            else:
                st.session_state.last_result = f"❌ Not quite. It was {current_word}"
            st.session_state.submitted = True
            st.session_state.show_next = True

    # ------------------ MULTIPLE CHOICE MODE ------------------
    else:
        st.markdown("### ❓ Choose the correct spelling:")
        options = [current_word] + current_word_details.get("spell", [])
        random.shuffle(options)
        col1, col2, col3 = st.columns(3)
        for i, opt in enumerate(options):
            col = [col1, col2, col3][i % 3]
            if col.button(opt, disabled=st.session_state.submitted):
                if not st.session_state.submitted:
                    if opt == current_word:
                        st.session_state.last_result = f"🌟 Correct! It was {current_word}"
                        st.session_state.score += 1
                    else:
                        st.session_state.last_result = f"❌ Not quite. It was {current_word}"
                    st.session_state.submitted = True
                    st.session_state.show_next = True

    # ------------------ FEEDBACK ------------------
    if st.session_state.last_result:
        st.write(st.session_state.last_result)

    # ------------------ NEXT WORD ------------------
    if st.session_state.show_next:
        if st.button("Next Word"):
            st.session_state.submitted = False
            st.session_state.show_next = False
            st.session_state.last_result = None
            st.session_state.mode = None
            st.session_state.index += 1
            if st.session_state.index >= len(st.session_state.words):
                st.session_state.done = True
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
