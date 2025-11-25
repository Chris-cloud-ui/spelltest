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
from streamlit_javascript import st_javascript

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
if "mc_submitted" not in st.session_state:
    st.session_state.mc_submitted = False
if "mc_choice" not in st.session_state:
    st.session_state.mc_choice = None
if "text_submitted" not in st.session_state:
    st.session_state.text_submitted = False
if "user_word" not in st.session_state:
    st.session_state.user_word = ""

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

    # Randomly choose input type if not already chosen
    if "mode" not in st.session_state:
        if "spell" in current_word_details and random.choice([True, False]):
            st.session_state.mode = "mc"
        else:
            st.session_state.mode = "text"

    # ---------------- TEXT INPUT MODE ----------------
    if st.session_state.mode == "text":
        st.markdown(f"### 🔊 Listen and spell the word:")

        # --- Audio TTS ---
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

        # --- Text input form ---
        with st.form(key="spell_form"):
            user_word = st.text_input(
                "Type the word:",
                key="user_word",
                placeholder="Type here",
                autocomplete="off"
            )
            button_label = "Next Word" if st.session_state.text_submitted else "Submit"
            submitted = st.form_submit_button(button_label)

        if submitted:
            if not st.session_state.text_submitted:
                # Check answer
                if user_word.upper() == current_word.upper():
                    st.success("🌟 Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Not quite. It was **{current_word}**.")
                st.session_state.text_submitted = True
            else:
                # Next word
                st.session_state.text_submitted = False
                st.session_state.user_word = ""
                st.session_state.index += 1
                st.session_state.mode = None
                if st.session_state.index >= len(st.session_state.words):
                    st.session_state.done = True
                st.experimental_rerun()
        st.write("Your spelling:", st.session_state.user_word)

    # ---------------- MULTIPLE CHOICE MODE ----------------
    elif st.session_state.mode == "mc":
        st.markdown("### ❓ Choose the correct spelling:")

        if "options" not in st.session_state:
            options = [current_word] + current_word_details.get("spell", [])
            random.shuffle(options)
            st.session_state.options = options

        def mc_button(label):
            if st.session_state.mc_submitted:
                if label == current_word:
                    color = "#4CAF50"  # green
                    icon = " ✅"
                elif label == st.session_state.mc_choice:
                    color = "#F44336"  # red
                    icon = " ❌"
                else:
                    color = "#007BFF"  # blue
                    icon = ""
            else:
                color = "#007BFF"
                icon = ""
            html = f"""
            <div style="margin-bottom:10px;">
                <button onclick="window.parent.postMessage({{'mc_choice':'{label}'}}, '*')" 
                    style="width:100%; background-color:{color}; color:white; border:none; padding:12px; font-size:18px; border-radius:6px;">
                    {label}{icon}
                </button>
            </div>
            """
            st.markdown(html, unsafe_allow_html=True)

        for opt in st.session_state.options:
            mc_button(opt)

        clicked = st_javascript("""
        return new Promise((resolve) => {
            window.addEventListener('message', (event) => {resolve(event.data.mc_choice)}, {once:true});
        });
        """)

        if clicked and not st.session_state.mc_submitted:
            st.session_state.mc_choice = clicked
            st.session_state.mc_submitted = True
            if clicked == current_word:
                st.session_state.score += 1

        if st.session_state.mc_submitted:
            if st.button("Next Word"):
                st.session_state.mc_submitted = False
                st.session_state.mc_choice = None
                st.session_state.options = None
                st.session_state.index += 1
                st.session_state.mode = None
                if st.session_state.index >= len(st.session_state.words):
                    st.session_state.done = True
                st.experimental_rerun()

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
