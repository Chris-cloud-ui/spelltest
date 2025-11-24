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
from streamlit_javascript import st_javascript
from random import randint

st_javascript("""
if (!window.hasKeyboardListener) {
    window.hasKeyboardListener = true;
    window.lastLetter = null;

    window.addEventListener("message", (event) => {
        if (event.data.letter) {
            window.lastLetter = event.data.letter;
            localStorage.setItem("lastLetter", event.data.letter);
        }
    });
}
""")

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
        help_text = " ".join(syllables)
        
        #helptext = gTTS(text=help_text, lang='en', tld='co.uk', slow=True)
        # 
        # --- Save to BytesIO ---
        #question_fp = io.BytesIO()
        #question.write_to_fp(question_fp)
        #quest=question_fp.seek(0)

        #help_fp = io.BytesIO()
        #helptext.write_to_fp(help_fp)
        #hell=help_fp.seek(0)
        
        
        #help_fp.seek(0)
    
        # # --- Load as AudioSegment and combine ---
        #audio_question = AudioSegment.from_file(quest, format="mp3")
        #audio_help = AudioSegment.from_file(hell, format="mp3")
        #combined = audio_question + audio_help
    
        # --- Export combined to BytesIO ---
        #combined_buffer = io.BytesIO()
        #combined.export(combined_buffer, format="mp3")
        #combined_buffer.seek(0)
    
        # --- Play in Streamlit ---
        #st.audio(combined_buffer, format='audio/mp3')
        
    else:
        st.write(current_word)
        #question_fp = io.BytesIO()
        #question.save(question_fp)
        #question_fp.seek(0)
        #st.audio(question_fp, format='audio/mp3')
        

    # st.write("Spell the word by tapping letters:")
    # query = st.text_input("Enter your query:", placeholder="Query...", autocomplete="off")
    # Initialize answer
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    # st.write("Your spelling:", st.session_state.answer)

    # Function to check the answer
    def submit_answer():
        current_word = st.session_state.current_word
        if st.session_state.answer.upper() == current_word.upper():
            st.success("🌟 Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Not quite. It was **{current_word}**.")
        

    
    user_input = st.text_input(
        "Type the word:", 
        key="answer",
        value="", 
        on_change=submit_answer, 
        help="Your typing will appear below"
    )

    # Update session state
    #if user_input:
    #    st.session_state.answer = user_input
    
    # Label showing typed letters
    # st.markdown(f"**You typed:** {st.session_state.answer}")
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    
    
    
    # Set current word in session_state so the callback can access it
    st.session_state.current_word = st.session_state.words[st.session_state.index]["word"]


    
    # components.html(html, height=150)
    
    


    #keyboard_html = """
    #<script>
    #function sendLetter(letter) {
    #    window.top.postMessage({letter: letter}, "*");
    #}
    #</script>
    
    #<div style="display:flex; flex-wrap:wrap; gap:6px; justify-content:center; max-width:400px;">
    #"""
    
    # Add letter buttons
    #for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ":
    #    keyboard_html += f"""
    #        <button onclick="sendLetter('{c}')" 
    #            style="flex:1 0 20%; padding:12px; font-size:20px;">
    #            {c}
    #        </button>
    #    """
    
    #keyboard_html += """
    #    <button onclick="sendLetter('BACK')" style="flex:1 0 45%; padding:12px; background:#f88;">⬅️ Backspace</button>
    #    <button onclick="sendLetter('SUBMIT')" style="flex:1 0 45%; padding:12px; background:#9f9;">Submit</button>
    #</div>
    #"""

    #components.html(keyboard_html, height=500)
    
    # --- LISTEN FOR POSTMESSAGES ---
    #clicked = st_javascript("""
    #return localStorage.getItem("lastLetter");
    #""")
    
    

    #letter = st_javascript("window.clicked")
    #if clicked:
    #     if clicked == "BACK":
    #        st.session_state.answer = st.session_state.answer[:-1]
    #    elif clicked == "SUBMIT":
    #        if st.session_state.answer.upper() == current_word.upper():
    #            st.success("🌟 Correct!")
    #            st.session_state.score += 1
    #        else:
    #            st.error(f"❌ Not quite. It was **{current_word}**.")
    #        
    #        st.session_state.answer = ""
    #        st.session_state.index += 1
    #        
    #        if st.session_state.index >= len(st.session_state.words):
    #            st.session_state.done = True
   
    #        st.rerun()
    #
    #    else:  # a letter
    #        st.session_state.answer += clicked

    
    


    # Backspace
    # cols = st.columns([1,1,1,1])
    # if cols[0].button("⬅️ Backspace"):
    #     st.session_state.answer = st.session_state.answer[:-1]
    # if cols[1].button("Submit"):
    #    if st.session_state.answer.upper() == current_word.upper():
    #        st.success("🌟 Correct!")
    #        st.session_state.score += 1
    #    else:
    #        st.error(f"❌ Not quite. It was **{current_word}**.")
    #    st.session_state.answer = ""  # reset
    #    st.session_state.index += 1
    
    #    if st.session_state.index >= len(st.session_state.words):
    #        st.session_state.done = True

    if st.button("Next Word"):
        st.session_state.answer = ""  # reset input
        st.session_state.index += 1
        if st.session_state.index >= len(st.session_state.words):
            st.session_state.done = True
        st.rerun()  # refresh the app with next word
       
    
    # Show current spelling
    # st.write("Your spelling:", st.session_state.answer)
    #st.session_state.answer = ""
    

    if st.session_state.index >= len(st.session_state.words):
        st.success("🎉 All words completed! Restarting...")
        st.session_state.current_word_index = 0
        random.shuffle(st.session_state.words)
    
   
    # --- Optional: Button to show next word ---
    

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




































