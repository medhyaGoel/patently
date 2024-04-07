import streamlit as st
from streamlit.logger import get_logger
import side_bar
import openai
import requests
from io import StringIO
import scraping

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

my_inv = st.file_uploader(
    "Upload a description of your invention!",
    type=["txt"],
    help="Scanned documents are not supported yet!",
)

other_inv = st.file_uploader(
    "Upload a patent to compare with your invention!",
    type=["txt"],
    help="Scanned documents are not supported yet!",
)

client = openai.AsyncClient(api_key=openai_api_key)
# Your specific set of instructions for the model
sys_instructions = """As a digital patent attorney, my primary task is to help users articulate and evaluate their 
invention's patentability through a structured conversation. Initially, I ask the user to describe their invention in 
detail. This is crucial for understanding the essence of the invention.

If a user uploads a document, I will review it to determine if the three basic questions regarding the invention's 
uniqueness, its field or application, and knowledge of similar inventions have been answered. If these questions are 
adequately addressed in the document, I will immediately proceed to generate five relevant boolean search terms for 
patent searches. If further clarification is needed, I may ask up to two additional follow-up questions, 
one at a time, to refine the search terms.

The search terms are intended to guide the user in performing patent searches to identify any similar existing 
patents or technologies. For the keyword searches, each term will consist of a maximum of two words inside quotation 
marks. If any quoted term comprises three words, replace the quotation marks with parentheses.  This streamlined 
process is designed to efficiently guide users towards generating actionable search terms, limiting the conversation 
to a maximum of two follow-up questions after reviewing a document."""

# Read the PDF document
if my_inv is not None and openai_api_key is not None:
    stringio = StringIO(my_inv.getvalue().decode('utf-8'))
    read_data = stringio.read()
    # MAYBE USE GUARDRAILS HERE?
    st.write(read_data)

    data = {
        "messages": [
            {
                "role": "system",
                "content": sys_instructions,
            },
            {"role": "user",
             "content": read_data}
        ],
        "model": "gpt-4-0125-preview",
    }
    url = "https://api.openai.com/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {openai_api_key}"
    }
    st.subheader("example keywords")
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        print("Response from OpenAI:", response.json())
        print('\n')
        print(response.json()['choices'][0]['message']['content'])
        st.write(response.json()['choices'][0]['message']['content'])
    else:
        print("Error:", response.status_code, response.text)

    # grab searches returned by gpt and grab relevant patents
    st.write(scraping.grab_patents('"Mobile" AND "smart"'))
