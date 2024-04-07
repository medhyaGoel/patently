import streamlit as st
import side_bar

side_bar.sidebar()
openai_api_key = st.session_state.get("OPENAI_API_KEY")
if not openai_api_key:
    st.warning(
        "Enter your OpenAI API key in the sidebar. You can get a key at"
        " https://platform.openai.com/account/api-keys."
    )

st.title('patently')
st.subheader('Figure out whether your invention is already out there.')

my_inv = st.file_uploader(
    "Upload a description of your invention!",
    type=["pdf", "docx", "txt"],
    help="Scanned documents are not supported yet!",
)

other_inv = st.file_uploader(
    "Upload a patent to compare with your invention!",
    type=["pdf", "docx", "txt"],
    help="Scanned documents are not supported yet!",
)

if not my_inv or (not my_inv and not other_inv):
    st.stop()

# if not is_open_ai_key_valid(openai_api_key, model):
#     st.stop()

