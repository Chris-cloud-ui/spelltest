import streamlit as st
import yaml
import json
import os
from datetime import datetime
import random
from gtts import gTTS
import pyphen
import io
import whisper
import streamlit.components.v1 as components

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
    # st.audio(f"https://api.streamelements.com/kappa/v2/speech?voice=Brian&text={current_word}")
    #  st.write(f"Spell: {current_word}")

    dic = pyphen.Pyphen(lang='en')

    syllables = dic.inserted(current_word).split('-')
    # st.write(f"Spell: {syllables}")
    if "syll" in current_word_details:
        syllables = current_word_details["syll"]

    question = gTTS(text="Spell: " + current_word, lang='en', tld='co.uk', slow=False)
    # question_file = f"{current_word}.mp3"
    # question.save(question_file)

    if len(syllables)>1:
        help = ""

        for i in syllables:
            help = help + i + " "
        helptext = gTTS(text=help, lang='en', tld='co.uk', slow=True)
        # helptext_file = f"{current_word}_help.mp3"
        # helptext.save(helptext_file)

        # -----------------------------
        # Combine both audio files
        # -----------------------------
        # audio_question = AudioSegment.from_file(question_file)
        # audio_help = AudioSegment.from_file(help_file)
        
        # combined = audio_question + audio_help
        # combined_file = f"{current_word}_combined.mp3"
        #  combined.export(combined_file, format="mp3")

        combined_audio = io.BytesIO()
        question.write_to_fp(combined_audio)
        helptext.write_to_fp(combined_audio)
        combined_audio.seek(0)

        st.audio(combined_audio, format='audio/mp3')
        
        # Use the combined file
        # st.audio(combined_file)
    else:
        question.save(f"{current_word}.mp3")
        st.audio(f"{current_word}.mp3")

    st.write("Spell the word by tapping letters:")

    # Initialize answer
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    
    # Function to add a letter
    def add_letter(letter):
        st.session_state.answer += letter
    
    # Keyboard layout
    keyboard_rows = [
        ["A","B","C","D","E","F"],
        ["G","H","I","J","K","L"],
        ["M","N","O","P","Q","R"],
        ["S","T","U","V","W","X"],
        ["Y","Z"]
    ]
    
    # Display buttons row by row
    for row in keyboard_rows:
        cols = st.columns(len(row))
        for col, letter in zip(cols, row):
            if col.button(letter):
                add_letter(letter)
    
    # Backspace
    cols = st.columns([1,1,1,1])
    if cols[0].button("⬅️ Backspace"):
        st.session_state.answer = st.session_state.answer[:-1]
    if cols[1].button("Submit"):
        current_word = "CAT"
        misspellings = ["KAT", "CATT"]
        allowed = [current_word.upper()] + [m.upper() for m in misspellings]
        if st.session_state.answer.upper() in allowed:
            st.success("Correct!")
        else:
            st.error(f"Incorrect. The word was: {current_word}")
        st.session_state.answer = ""  # reset
    
    # Show current spelling
    st.write("Your spelling:", st.session_state.answer)

    if answer:
        if answer.lower().strip() == current_word.lower():
            st.success("🌟 Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Not quite. It was **{current_word}**.")

        st.session_state.index += 1
    
        if st.session_state.index >= len(st.session_state.words):
            st.session_state.done = True
    
    # --- Optional: Button to show next word ---
    if st.button("Next Word"):
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

























