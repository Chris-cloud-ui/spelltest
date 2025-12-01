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

HISTORY_FILE = "spells.json"
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
if "scoretwo" not in st.session_state:
    st.session_state.scoretwo = 0
if "done" not in st.session_state:
    st.session_state.done = False
if "words" not in st.session_state:
    words = WORD_LISTS[list_choice][:]
    if shuffle:
        random.shuffle(words)
    st.session_state.words = words
    st.session_state.originalwords = words
if "redo_words" not in st.session_state:
    st.session_state.redo_words = []
if "in_round_2" not in st.session_state:
    st.session_state.in_round_2 = False

# Per-word state
if "submitted" not in st.session_state:
    st.session_state.submitted = False
if "current_mode" not in st.session_state:
    st.session_state.current_mode = None
if "audio_file" not in st.session_state:
    st.session_state.audio_file = None

# Multiple choice specific
if "mc_options" not in st.session_state:
    st.session_state.mc_options = None
if "mc_selection" not in st.session_state:
    st.session_state.mc_selection = None

# Misspelt words
if "misspelt" not in st.session_state:
    st.session_state.misspelt = ""
    
# ------------------ HEADER ------------------------
st.markdown("""
    <h1 style='text-align:center; color:#ff66a6;'>
        🧙‍♀️ Slay Spells
    </h1>
""", unsafe_allow_html=True)

# ------------------ AUDIO HELPERS ------------------
AUDIO_DIR = "audio"
os.makedirs(AUDIO_DIR, exist_ok=True)

def get_audio_for_word(word, syllables=None):
    safe_name = word.replace(" ", "_").lower()
    filename = os.path.join(AUDIO_DIR, f"{safe_name}.mp3")
    # To deal with redoing the mp3
    #if safe_name == "criticise":
    #    st.info("Redo")
    #else:
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
    if len(st.session_state.words) > 0:
        fixes = len(st.session_state.words)
        score = st.session_state.score
        scoretwo = st.session_state.scoretwo
        total = len(st.session_state.originalwords)
        misspellings = st.session_state.misspelt
        st.success(f"📊 All done!")
        if st.session_state.in_round_2:
            st.success(f"⭐ You scored **{scoretwo} / {total}**")
            st.success(f"🔧 You fixed **{score} / {fixes}**")
            scoretext = f"{scoretwo} / {total}"
            fixtext = f"{score} / {fixes}"
        else:
            st.success(f"⭐ You scored **{score} / {total}**")
            scoretext = f"{score} / {total}"
            fixtext = f"0 / 0"
        
        save_history({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "list": list_choice,
            "score": scoretext,
            "fixes": fixtext,
            "misspellings": misspellings
        })
        st.balloons()
        st.session_state.words = []
else:
    current_word_details = st.session_state.words[st.session_state.index]
    current_word = current_word_details["word"]
    qnum = st.session_state.index + 1
    total = len(st.session_state.words)
    # Pick mode once per word
    if st.session_state.current_mode is None:
        if "spell" in current_word_details:
            st.session_state.current_mode = random.choice(["text", "mc", "ml"])
        else:
            st.session_state.current_mode = random.choice(["text", "ml"])
        st.session_state.current_mode="ml"
        st.session_state.submitted = False
        st.session_state.audio_file = None

    dic = pyphen.Pyphen(lang="en")
    syllables = dic.inserted(current_word).split("-")
    if "syll" in current_word_details: 
        syllables = current_word_details["syll"]
    mp3_file = get_audio_for_word(current_word, syllables)
    # ------------------ TEXT INPUT MODE ------------------
    if st.session_state.current_mode == "text":
        
        
        
        
        if st.session_state.in_round_2:
            st.markdown(f"#### 🔊 Let's correct the misspelled words! ####")
            st.error(f"Fix {qnum} of {total}")
        else:
            st.markdown(f"### 🔊 Listen and spell:")
            st.info(f"Question {qnum} of {total}")
        
        
        
        if "user_word_value" not in st.session_state:
            st.session_state.user_word_value = ""
        if "submitted" not in st.session_state:
            st.session_state.submitted = False
            
        # Form for text input
        if not st.session_state.submitted:
            st.audio(mp3_file)
            with st.form(key="text_form"):
                user_word = st.text_input(
                    "🪄",
                    value="", #st.session_state.user_word_value,  
                    key=current_word,
                    placeholder="Type here",
                    autocomplete="off"
                )
                submitted = st.form_submit_button("Submit", disabled=st.session_state.submitted)
                
            if submitted and len(user_word) > 0:
                st.session_state.submitted = True
                st.session_state.user_word_value = user_word     # store answer

                if user_word.upper() == current_word.upper():
                    st.session_state.score += 1
                    st.session_state.correct = True
                    
                else:
                    if not st.session_state.in_round_2:
                        st.session_state.misspelt += "<br>           " + current_word + " (typed: " + user_word.lower() + ")"
                    st.session_state.redo_words.append(current_word_details)
                    st.session_state.correct = False
                    #
                st.rerun()
        else:
            
            if st.session_state.correct:
                st.success(f"Correct. It was **{current_word}**.", icon="🪄")
            else:
                st.error(f"Not quite. It was **{current_word}**.", icon="❌")
                    
            st.info("Current score: " + str(st.session_state.score) + " out of " + str(st.session_state.index + 1))
                    
            # st.session_state.submitted = True
            if st.button("Next Word"):

                st.session_state.index += 1
                st.session_state.current_mode = None
                st.session_state.submitted = False
                st.session_state.user_word_value = ""
             
                if st.session_state.index >= len(st.session_state.words):
                    # ---------- ROUND 1 FINISHED ----------
                    if not st.session_state.in_round_2:
                        
                        if len(st.session_state.redo_words) > 0:
                            st.session_state.scoretwo = st.session_state.score
                            
                            # Start Round 2
                            st.session_state.words = st.session_state.redo_words[:]
                            st.session_state.redo_words = []
                            st.session_state.in_round_2 = True
                
                            # Option A — keep Round 1 score
                            # (do nothing to score)
                
                            # Option B — reset score for Round 2
                            st.session_state.score = 0
                
                            st.session_state.index = 0
                            st.session_state.current_mode = None
                            st.session_state.submitted = False
                
                            st.success("✨ Round 2: Let's correct the misspelled words!")
                            st.rerun()
                
                        else:
                            st.session_state.done = True
                
                    # ---------- ROUND 2 FINISHED ----------
                    else:
                        st.session_state.done = True
        
                st.rerun()
        

    # ------------------ MULTIPLE CHOICE MODE ------------------
    elif st.session_state.current_mode == "mc":
        if st.session_state.in_round_2:
            st.markdown(f"#### ❓ Let's correct the misspelled words! ####")
            st.error(f"Fix {qnum} of {total}")
        else:
            st.markdown(f"### ❓ Choose the spelling:")
            st.info(f"Question {qnum} of {total}")
        correct = current_word
        options = [correct] + current_word_details.get("spell", [])
    
        # Shuffle options once per word
        if st.session_state.mc_options is None:
            random.shuffle(options)
            st.session_state.mc_options = options
            st.session_state.mc_selection = None
    
        # Use radio buttons inside a form
        if not st.session_state.submitted:
            st.audio(mp3_file)
            with st.form(key="mc_form"):
                st.session_state.mc_selection = st.radio(
                    "", st.session_state.mc_options, index=0
                )
                submitted = st.form_submit_button("Submit", disabled=st.session_state.submitted)
            if submitted:
                st.session_state.submitted = True
                selected = st.session_state.mc_selection
                if selected.upper() == current_word.upper():
                    st.session_state.score += 1
                    st.session_state.correct = True
                else:
                    st.session_state.correct = False
                    if not st.session_state.in_round_2:
                        st.session_state.misspelt += "<br>           " + current_word + f" (selected: {selected})"
                    st.session_state.redo_words.append(current_word_details)
                st.rerun()

        else:
            if st.session_state.correct:
                st.success(f"Correct. It was **{current_word}**.", icon="🪄")
            else:
                st.error(f"Not quite. It was **{current_word}**.", icon="❌")
                    
            st.info("Current score: " + str(st.session_state.score) + " out of " + str(st.session_state.index + 1))

            if st.button("Next Word"):

                st.session_state.index += 1
                st.session_state.current_mode = None
                st.session_state.submitted = False
                st.session_state.mc_options = None
                st.session_state.mc_selection = None
             
                if st.session_state.index >= len(st.session_state.words):
                    # ---------- ROUND 1 FINISHED ----------
                    if not st.session_state.in_round_2:
                        st.session_state.scoretwo = st.session_state.score
                        if len(st.session_state.redo_words) > 0:
                            # Start Round 2
                            st.session_state.words = st.session_state.redo_words[:]
                            st.session_state.redo_words = []
                            st.session_state.in_round_2 = True
                
                            # Option A — keep Round 1 score
                            # (do nothing to score)
                
                            # Option B — reset score for Round 2
                            st.session_state.score = 0
                
                            st.session_state.index = 0
                            st.session_state.current_mode = None
                            st.session_state.submitted = False
                
                            st.success("✨ Round 2: Let's correct the misspelled words!")
                            st.rerun()
                
                        else:
                            st.session_state.done = True
                
                    # ---------- ROUND 2 FINISHED ----------
                    else:
                        st.session_state.done = True
        
                st.rerun()
    # ------------------ MISSING LETTER MODE ------------------
    else:
        if st.session_state.in_round_2:
            st.markdown(f"#### ❓ Let's correct the misspelled words! ####")
            st.error(f"Fix {qnum} of {total}")
        else:
            st.markdown(f"### ❓ Fill the missing letters:")
            st.info(f"Question {qnum} of {total}")
        correct = current_word
        options = [correct] + current_word_details.get("spell", [])
        missing_indices = sorted(random.sample(range(len(current_word)), 3))
        user_letters = {}
        display_word = ""
        
        
        
        
        letters=["A","B","C","D","E","F","G","H","I","J","K","L","M","N","O","P","Q","R","S","T","U","V","W","X","Y","Z"]
        # Use radio buttons inside a form
        if not st.session_state.submitted:
            st.audio(mp3_file)
            with st.form(key="mc_form"):
                for i, letter in enumerate(current_word):
                    if i in missing_indices:
                        key = f"letter_{i}"
                        # Initialize session_state if not present
                        if key not in st.session_state:
                            st.session_state[key] = ""  # empty default
                
                        # Dropdown with persisted value
                        user_letters[i] = st.selectbox(
                            f"Letter {i+1}",
                            options=letters,
                            index=letters.index(st.session_state[key]) if st.session_state[key] in letters else 0,
                            key=key
                        )
                        # Update session_state
                        st.session_state[key] = user_letters[i]
                
                        display_word += "_"
                    else:
                        display_word += letter
                st.success(f"Word to fill: {display_word}")
                submitted = st.form_submit_button("Submit", disabled=st.session_state.submitted)
            if submitted:
                st.session_state.submitted = True
                correct = True
                for i in missing_indices:
                    if st.session_state[f"letter_{i}"].upper() != word[i]:
                        correct = False
                        break
                
                if correct:
                    st.session_state.score += 1
                    st.session_state.correct = True
                else:
                    st.session_state.correct = False
                    if not st.session_state.in_round_2:
                        st.session_state.misspelt += "<br>           " + current_word + f" (todo)"
                    st.session_state.redo_words.append(current_word_details)
                #st.rerun()

        else:
            if st.session_state.correct:
                st.success(f"Correct. It was **{current_word}**.", icon="🪄")
            else:
                st.error(f"Not quite. It was **{current_word}**.", icon="❌")
                    
            st.info("Current score: " + str(st.session_state.score) + " out of " + str(st.session_state.index + 1))

            if st.button("Next Word"):

                st.session_state.index += 1
                st.session_state.current_mode = None
                st.session_state.submitted = False
             
                if st.session_state.index >= len(st.session_state.words):
                    # ---------- ROUND 1 FINISHED ----------
                    if not st.session_state.in_round_2:
                        st.session_state.scoretwo = st.session_state.score
                        if len(st.session_state.redo_words) > 0:
                            # Start Round 2
                            st.session_state.words = st.session_state.redo_words[:]
                            st.session_state.redo_words = []
                            st.session_state.in_round_2 = True
                
                            # Option A — keep Round 1 score
                            # (do nothing to score)
                
                            # Option B — reset score for Round 2
                            st.session_state.score = 0
                
                            st.session_state.index = 0
                            st.session_state.current_mode = None
                            st.session_state.submitted = False
                
                            st.success("✨ Round 2: Let's correct the misspelled words!")
                            st.rerun()
                
                        else:
                            st.session_state.done = True
                
                    # ---------- ROUND 2 FINISHED ----------
                    else:
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
            ⭐ Score: **{entry['score']}**
            <br>
            🔧 Fixes: **{entry['fixes']}**
            <br>
            🔤 Misspellings: {entry['misspellings']} 
            <br><br>
        """, unsafe_allow_html=True)












































































































































