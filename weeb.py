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

# Per-word state
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

# ------------------ HEADER ------------------------
st.markdown("""
    <h1 style='text-align:center; color:#ff66a6;'>
        🧙‍♀️ Slay Spells
    </h1>
    <p style='text-align:center; font-size:20px; color:#555;'>
        Practise your spells
    </p>
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
    current_word_details = st.session_state.words[st.session_state.index]
    current_word = current_word_details["word"]

    # Pick mode once per word
    if st.session_state.current_mode is None:
        if "spell" in current_word_details:
            st.session_state.current_mode = random.choice(["text", "mc"])
        else:
            st.session_state.current_mode = "text"
        st.session_state.submitted = False
        st.session_state.audio_file = None

    # ------------------ TEXT INPUT MODE ------------------
    if st.session_state.current_mode == "text":
        st.markdown(f"### 🔊 Listen and spell the word:")

        dic = pyphen.Pyphen(lang="en")
        syllables = dic.inserted(current_word).split("-")
        if "syll" in current_word_details: 
            syllables = current_word_details["syll"]
        mp3_file = get_audio_for_word(current_word, syllables)
        st.audio(mp3_file)
        
        if "user_word_value" not in st.session_state:
            st.session_state.user_word_value = ""
            
        # Form for text input
        with st.form(key="text_form"):
            user_word = st.text_input(
                "Type the word:",
                value=st.session_state.user_word_value,  
                placeholder="Type here",
                autocomplete="off"
            )
            # Change label depending on state
            btn_label = "Next Word" if st.session_state.submitted else "Submit"
            submitted = st.form_submit_button(btn_label)

        if submitted:
            if not st.session_state.submitted:
                # Check answer
                if user_word.upper() == current_word.upper():
                    st.success("🌟 Correct!")
                    st.session_state.score += 1
                else:
                    st.error(f"❌ Not quite. It was **{current_word}**.")
                st.session_state.submitted = True
                st.session_state.user_word_value = user_word  # Keep visible
            else:
                # Next word
                st.session_state.index += 1
                st.session_state.current_mode = None
                st.session_state.submitted = False
                st.session_state.user_word_value = ""  # Clear text safely
                if st.session_state.index >= len(st.session_state.words):
                    st.session_state.done = True
                st.rerun()

    # ------------------ MULTIPLE CHOICE MODE ------------------
    else:
        st.markdown(f"### ❓ Choose the correct spelling:")
        # Build options
        correct = current_word
        options = [correct]
        if "spell" in current_word_details:
            options += current_word_details["spell"]
        
        # Shuffle only once per word
        if "mc_options" not in st.session_state:
            random.shuffle(options)
            st.session_state.mc_options = options


        # Render buttons manually with HTML + JS for styling
        for idx, option in enumerate(st.session_state.mc_options):
            color = "white"
            if st.session_state.submitted:
                if option == correct:
                    color = "#28a745" if st.session_state.mc_selection == option else "white"
                elif st.session_state.mc_selection == option:
                    color = "#dc3545"
            # Full width button
            btn_html = f"""
            <form action="?" method="post">
            <input type="submit" name="mc_{idx}" value="{option}" 
                style="background-color:{color}; color:{ 'white' if color!='white' else 'black'}; width:100%; padding:10px; margin:5px 0; border:none; font-size:16px;">
            </form>
            """
            st.markdown(btn_html, unsafe_allow_html=True)
    
        # Handle clicks
        clicked_idx = None
        for idx in range(len(st.session_state.mc_options)):
            if st_javascript(f"return window.event && window.event.submitter && window.event.submitter.name == 'mc_{idx}';"):
                clicked_idx = idx
                break
    
        if clicked_idx is not None and not st.session_state.submitted:
            selected_option = st.session_state.mc_options[clicked_idx]
            st.session_state.mc_selection = selected_option
            st.session_state.submitted = True
            if selected_option == correct:
                st.success("✅ Correct!")
                st.session_state.score += 1
            else:
                st.error("❌ Not quite.")
    
        elif st.session_state.submitted and clicked_idx is not None:
            # Move to next word
            st.session_state.index += 1
            st.session_state.current_mode = None
            st.session_state.submitted = False
            st.session_state.mc_options = None
            st.session_state.mc_selection = None
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








