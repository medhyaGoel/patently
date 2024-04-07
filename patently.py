import streamlit as st
from streamlit.logger import get_logger
import side_bar
import openai

logger = get_logger(__name__)

side_bar.sidebar()
openai_api_key = st.session_state.get("OPENAI_API_KEY")
if not openai_api_key:
    st.warning(
        "Enter your OpenAI API key in the sidebar. You can get a key at"
        " https://platform.openai.com/account/api-keys."
    )

st.title('patently')
st.subheader('Figure out whether your invention is already out there.')

def is_open_ai_key_valid(openai_api_key, model: str) -> bool:
    if model == "debug":
        return True

    if not openai_api_key:
        st.error("Please enter your OpenAI API key in the sidebar!")
        return False
    try:
        openai.ChatCompletion.create(
            model=model,
            messages=[{"role": "user", "content": "test"}],
            api_key=openai_api_key,
        )
    except Exception as e:
        st.error(f"{e.__class__.__name__}: {e}")
        logger.error(f"{e.__class__.__name__}: {e}")
        return False

    return True

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



if not is_open_ai_key_valid(openai_api_key, model):
    st.stop()


