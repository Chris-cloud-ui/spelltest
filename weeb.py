import streamlit as st
from streamlit_javascript import st_javascript
import streamlit.components.v1 as components

st.title("🔧 Keyboard Test")

# -------------------------
# JS LISTENER (main window)
# -------------------------
st_javascript("""
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
""")

# -------------------------
# HTML BUTTONS (iframe)
# -------------------------
html = """
<script>
function sendLetter(letter) {
    console.log("Sending:", letter);
    window.top.postMessage({letter: letter}, "*");
}
</script>

<div style="display:flex; flex-wrap:wrap; gap:10px;">
    <button onclick="sendLetter('A')" style="padding:20px;">A</button>
    <button onclick="sendLetter('B')" style="padding:20px;">B</button>
    <button onclick="sendLetter('C')" style="padding:20px;">C</button>
</div>
"""

components.html(html, height=200)

# -------------------------
# READ LAST LETTER
# -------------------------
letter = st_javascript("return localStorage.getItem('lastLetter');")

st.write("**Last letter clicked:**", letter)

if letter:
    st_javascript("localStorage.setItem('lastLetter', '')")
