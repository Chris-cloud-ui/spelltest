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
import streamlit.components.v1 as components
from streamlit_javascript import st_javascript
from random import randint


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
    current_word=current_word_details["word"]

    st.markdown(f"### 🔊 Listen and spell the word:")

    dic = pyphen.Pyphen(lang='en')

    syllables = dic.inserted(current_word).split('-')
    if "syll" in current_word_details:
        syllables = current_word_details["syll"]

    # --- Helper to generate MP3 as bytes ---
    def tts_bytes(text, slow=False):
        fp = io.BytesIO()
        tts = gTTS(text=text, lang="en", tld="co.uk", slow=slow)
        tts.write_to_fp(fp)
        fp.seek(0)
        return fp.read()   # return raw mp3 bytes
    
    # --- Build the final MP3 ---
    final_mp3 = b""
    
    # 1. Main question
    final_mp3 += tts_bytes(f"Can you spell {current_word}?", slow=False)
    
    # 2. Syllables (slow)
    if len(syllables) > 1:
        for s in syllables:
            final_mp3 += tts_bytes(s, slow=True)
    
    # 3. Save to temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp:
        tmp.write(final_mp3)
        temp_filename = tmp.name
    
    # 4. Play in Streamlit
    st.audio(temp_filename)



    # Initialize answer
    if "answer" not in st.session_state:
        st.session_state.answer = ""

    # Function to check the answer
    if "score" not in st.session_state:
        st.session_state.score = 0
    
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    
    with st.form(key="spell_form"):
        user_word = st.text_input(
            "Type the word:", 
            value="", 
            placeholder="Type here", 
            autocomplete="off"
        )
        submitted = st.form_submit_button("Submit")
    
    if submitted:
        if user_word.upper() == current_word.upper():
            st.success("🌟 Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Not quite. It was **{current_word}**.")
        st.session_state.answer = user_word
    st.write("Your spelling:", st.session_state.answer)
    
    
    
    
    # Set current word in session_state so the callback can access it
    st.session_state.current_word = st.session_state.words[st.session_state.index]["word"]



    if st.button("Next Word"):
        st.session_state.answer = ""  # reset input
        st.session_state.index += 1
        if st.session_state.index >= len(st.session_state.words):
            st.session_state.done = True
        st.rerun()  # refresh the app with next word


    if st.session_state.index >= len(st.session_state.words):
        st.success("🎉 All words completed! Restarting...")
        st.session_state.current_word_index = 0
        random.shuffle(st.session_state.words)

    

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





















































