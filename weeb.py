import streamlit as st
from streamlit_javascript import st_javascript
import streamlit.components.v1 as components

st.title("🔧 Keyboard Test")

# ---------------------------------
# INSTALL LISTENER ON MAIN WINDOW
# ---------------------------------
st_javascript("""
(() => {
    if (!window.hasKeyboardListener) {
        window.hasKeyboardListener = true;
        console.log("Listener installed!");

        window.addEventListener("message", (event) => {
            console.log("Message received:", event.data);
            if (event.data.letter) {
                localStorage.setItem("lastLetter", event.data.letter);
            }
        });
    }
})();
""")

# ---------------------------------
# KEYBOARD INSIDE IFRAME
# ---------------------------------
components.html("""
<script>
function sendLetter(letter) {
    console.log("Sending:", letter);
    window.top.postMessage({letter: letter}, "*");
}
</script>

<div style="display:flex; gap:10px;">
    <button onclick="sendLetter('A')" style="padding:20px;">A</button>
    <button onclick="sendLetter('B')" style="padding:20px;">B</button>
    <button onclick="sendLetter('C')" style="padding:20px;">C</button>
</div>
""", height=150)

# ---------------------------------
# READ lastLetter FROM localStorage
# ---------------------------------
letter = st_javascript("""
(async () => {
    return localStorage.getItem('lastLetter');
})();
""")

st.write("**Last letter clicked:**", letter)

# Reset after reading
if letter:
    st_javascript("""
    (() => { localStorage.setItem('lastLetter', ''); })();
    """)
