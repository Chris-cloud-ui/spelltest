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
        print (help_text)
        
        # helptext = gTTS(text=help_text, lang='en', tld='co.uk', slow=True)
        # 
        # # --- Save to BytesIO ---
        # question_fp = io.BytesIO()
        # help_fp = io.BytesIO()
        # question.write_to_fp(question_fp)
        # helptext.write_to_fp(help_fp)
        # question_fp.seek(0)
        # help_fp.seek(0)
    
        # # --- Load as AudioSegment and combine ---
        # audio_question = AudioSegment.from_file(question_fp, format="mp3")
        # audio_help = AudioSegment.from_file(help_fp, format="mp3")
        # combined = audio_question + audio_help
    
        # # --- Export combined to BytesIO ---
        # combined_buffer = io.BytesIO()
        # combined.export(combined_buffer, format="mp3")
        # combined_buffer.seek(0)
    
        # # --- Play in Streamlit ---
        # st.audio(combined_buffer, format='audio/mp3')
        
    else:
        print ("single syllable")
        
        # question_fp = io.BytesIO()
        # question.write_to_fp(question_fp)
        # question_fp.seek(0)
        # st.audio(question_fp, format='audio/mp3')
        

    st.write("Spell the word by tapping letters:")
    # query = st.text_input("Enter your query:", placeholder="Query...", autocomplete="off")
    # Initialize answer
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    
    # Function to add a letter
    def add_letter(letter):
        st.write("al")
        st.session_state.answer += letter


    if "keyboard_letter" not in st.session_state:
        st.session_state.keyboard_letter = ""


    keyboard_html = f"""
    <div style="display: flex; flex-wrap: wrap; gap: 5px; justify-content: center; max-width: 400px; margin:auto;">
      {"".join([f'<button style="flex:1 0 20%; padding:10px; margin:2px; font-size:20px;" onclick="document.getElementById(\'hidden_input\').value+=\'{c}\'">{c}</button>' for c in "ABCDEFGHIJKLMNOPQRSTUVWXYZ"])}
      <button style="flex:1 0 45%; padding:10px; margin:2px; font-size:18px; background-color:#f99;" onclick="document.getElementById('hidden_input').value = document.getElementById('hidden_input').value.slice(0,-1)">⬅️ Backspace</button>
      <button style="flex:1 0 45%; padding:10px; margin:2px; font-size:18px; background-color:#9f9;" onclick="document.getElementById('hidden_input').dispatchEvent(new Event('change'))">Submit</button>
    </div>
    
    <input type="text" id="hidden_input" style="display:none;" value="{st.session_state.answer}" onchange="window.parent.postMessage({{letter:this.value}}, '*')">
    """
    
    # --- Define JS keyboard HTML ---
    keyboard_htmlold = """
    <div style="display: flex; flex-wrap: wrap; gap: 5px; justify-content: center;">
      <button onclick="sendLetter('A')">A</button>
      <button onclick="sendLetter('B')">B</button>
      <button onclick="sendLetter('C')">C</button>
      <button onclick="sendLetter('D')">D</button>
      <button onclick="sendLetter('E')">E</button>
      <button onclick="sendLetter('F')">F</button>
      <button onclick="sendLetter('G')">G</button>
      <button onclick="sendLetter('H')">H</button>
      <button onclick="sendLetter('I')">I</button>
      <button onclick="sendLetter('J')">J</button>
      <button onclick="sendLetter('K')">K</button>
      <button onclick="sendLetter('L')">L</button>
      <button onclick="sendLetter('M')">M</button>
      <button onclick="sendLetter('N')">N</button>
      <button onclick="sendLetter('O')">O</button>
      <button onclick="sendLetter('P')">P</button>
      <button onclick="sendLetter('Q')">Q</button>
      <button onclick="sendLetter('R')">R</button>
      <button onclick="sendLetter('S')">S</button>
      <button onclick="sendLetter('T')">T</button>
      <button onclick="sendLetter('U')">U</button>
      <button onclick="sendLetter('V')">V</button>
      <button onclick="sendLetter('W')">W</button>
      <button onclick="sendLetter('X')">X</button>
      <button onclick="sendLetter('Y')">Y</button>
      <button onclick="sendLetter('Z')">Z</button>
    </div>
    
    <script>
    function sendLetter(letter) {
        const msg = { letter: letter };
        window.parent.postMessage({func:'add_letter', data: msg}, '*');
    }
    </script>
    """

    components.html(keyboard_html, height=250)

    

    letter = st_javascript.eval_js("window.clicked")
    if letter:
        st.session_state.answer = letter
    
    st.write("Your spelling:", st.session_state.answer)

    
    clicked_letter = st.experimental_get_query_params().get("letter")
    if clicked_letter:
        st.write("cl")
        st.session_state.answer += clicked_letter[0]
    
    st.write("Your spelling:", st.session_state.answer)

    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
      <button onclick="window.parent.postMessage({func:'add_letter', letter:'A'}, '*')">A</button>
      <button onclick="Streamlit.setComponentValue('B')">B</button>
      <button onclick="Streamlit.setComponentValue('C')">C</button>
      <button onclick="Streamlit.setComponentValue('D')">D</button>
      <button onclick="Streamlit.setComponentValue('E')">E</button>
      <button onclick="Streamlit.setComponentValue('F')">F</button>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
      <button onclick="Streamlit.setComponentValue('G')">G</button>
      <button onclick="Streamlit.setComponentValue('H')">H</button>
      <button onclick="Streamlit.setComponentValue('I')">I</button>
      <button onclick="Streamlit.setComponentValue('J')">J</button>
      <button onclick="Streamlit.setComponentValue('K')">K</button>
      <button onclick="Streamlit.setComponentValue('L')">L</button>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
      <button onclick="Streamlit.setComponentValue('M')">M</button>
      <button onclick="Streamlit.setComponentValue('N')">N</button>
      <button onclick="Streamlit.setComponentValue('O')">O</button>
      <button onclick="Streamlit.setComponentValue('P')">P</button>
      <button onclick="Streamlit.setComponentValue('Q')">Q</button>
      <button onclick="Streamlit.setComponentValue('R')">R</button>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
      <button onclick="Streamlit.setComponentValue('S')">S</button>
      <button onclick="Streamlit.setComponentValue('T')">T</button>
      <button onclick="Streamlit.setComponentValue('U')">U</button>
      <button onclick="Streamlit.setComponentValue('V')">V</button>
      <button onclick="Streamlit.setComponentValue('W')">W</button>
      <button onclick="Streamlit.setComponentValue('X')">X</button>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style="display: flex; flex-wrap: wrap; justify-content: center;">
      <button onclick="Streamlit.setComponentValue('Y')">Y</button>
      <button onclick="Streamlit.setComponentValue('Z')">Z</button>
    </div>
    """, unsafe_allow_html=True)
    
    
    
    # Backspace
    cols = st.columns([1,1,1,1])
    if cols[0].button("⬅️ Backspace"):
        st.session_state.answer = st.session_state.answer[:-1]
    if cols[1].button("Submit"):
        if st.session_state.answer.upper() == current_word.upper():
            st.success("🌟 Correct!")
            st.session_state.score += 1
        else:
            st.error(f"❌ Not quite. It was **{current_word}**.")
        st.session_state.answer = ""  # reset
        st.session_state.index += 1
    
        if st.session_state.index >= len(st.session_state.words):
            st.session_state.done = True
        else:
            st.rerun()  # refresh the app with next word
    
    # Show current spelling
    st.write("Your spelling:", st.session_state.answer)
    #st.session_state.answer = ""
    

    if st.session_state.index >= len(st.session_state.words):
        st.success("🎉 All words completed! Restarting...")
        st.session_state.current_word_index = 0
        random.shuffle(st.session_state.words)
    
   
    # --- Optional: Button to show next word ---
    #if st.button("Next Word"):
    #    st.experimental_rerun()


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




























































