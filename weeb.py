import streamlit as st
import yaml
import json
import os
import random
from datetime import datetime
from gtts import gTTS
import pyphen
import io

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
    st.rerun()

# ------------------ SESSION STATE INIT ------------------
if "index" not in st.session_state: st.session_state.index = 0
if "score" not in st.session_state: st.session_state.score = 0
if "done" not in st.session_state: st.session_state.done = False
if "words" not in st.session_state:
    words = WORD_LISTS[list_choice][:]
    if shuffle: random.shuffle(words)
    st.session_state.words = words
if "submitted" not in st.session_state: st.session_state.submitted = False
if "answer" not in st.session_state: st.session_state.answer = ""

# ------------------ HEADER ------------------------
st.markdown("""
<h1 style='text-align:center; color:#ff66a6;'>🧙‍♀️ Slay Spells</h1>
<p style='text-align:center; font-size:20px; color:#555;'>Practise your spells</p>
""", unsafe_allow_html=True)

# ------------------ AUDIO HELPERS ------------------
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def get_audio_for_word(word, syllables=None):
    safe_name = word.replace(" ", "_").lower()
    filename = os.path.join(AUDIO_DIR, f"{safe_name}.mp3")
    if os.path.exists(filename):
        return filename
    # Generate MP3
    final_bytes = b""
    def tts_bytes(text, slow=False):
        fp = io.BytesIO()
        tts = gTTS(text=text, lang="en", tld="co.uk", slow=slow)
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()
    final_bytes += tts_bytes(f"Can you spell {word}?")
    if syllables and len(syllables) > 1:
        for s in syllables:
            final_bytes += tts_bytes(s, slow=True)
    with open(filename, "wb") as f:
        f.write(final_bytes)
    return filename

# ------------------ MAIN APP ----------------------
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
    word_entry = st.session_state.words[st.session_state.index]
    current_word = word_entry["word"]

    # Decide randomly: text input or multiple choice
    is_multiple_choice = "spell" in word_entry and random.choice([True, False])

    if is_multiple_choice:
        st.markdown("❓ **Choose the correct spelling:**")
        options = [current_word] + word_entry["spell"]
        random.shuffle(options)

        # Track selected button
        if "selected_option" not in st.session_state: st.session_state.selected_option = None

        # Show buttons
        for i, opt in enumerate(options):
            if st.session_state.selected_option == i:
                if opt == current_word:
                    style = "background-color:green;color:white;"
                    label = f"✔️ {opt}"
                else:
                    style = "background-color:red;color:white;"
                    label = f"❌ {opt}"
            else:
                style = "width:100%;padding:12px;margin-bottom:4px;"
                label = opt
            clicked = st.button(label, key=f"mc_{i}", help=None)
            if clicked and st.session_state.selected_option is None:
                st.session_state.selected_option = i
                if options[i] == current_word:
                    st.session_state.score += 1
        # Move to next word
        if st.session_state.selected_option is not None:
            if st.button("Next Word"):
                st.session_state.selected_option = None
                st.session_state.submitted = False
                st.session_state.index += 1
                if st.session_state.index >= len(st.session_state.words):
                    st.session_state.done = True
                st.rerun()

    else:
        # TEXT INPUT MODE
        dic = pyphen.Pyphen(lang="en")
        syllables = dic.inserted(current_word).split("-")
        if "syll" in word_entry: syllables = word_entry["syll"]
        mp3_file = get_audio_for_word(current_word, syllables)
        st.audio(mp3_file)

        with st.form(key="spell_form"):
            user_word = st.text_input("Type the word:", key="user_word", placeholder="Type here", autocomplete="off")
            button_label = "Next Word" if st.session_state.submitted else "Submit"
            submitted = st.form_submit_button(button_label)

        if submitted:
            if not st.session_state.submitted:
                # Check answer
                if user_word.upper() == current_word.upper():
                    st.success("🌟 Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Not quite. It was **{current_word}**.")
                st.session_state.answer = user_word
                st.session_state.submitted = True
            else:
                # NEXT WORD
                st.session_state.user_word = ""  # Reset text box
                st.session_state.submitted = False
                st.session_state.answer = ""
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
        """, unsafe_allow_html=True)
