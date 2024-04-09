import streamlit as st
from dotenv import load_dotenv
from streamlit.logger import get_logger
import side_bar
import requests
from io import StringIO
import scraping
# from guardrails import Guard
# from guardrails.hub import DetectPromptInjection
import json
import openai
import compare

load_dotenv()

logger = get_logger(__name__)

side_bar.sidebar()
openai_api_key = st.session_state.get("OPENAI_API_KEY")

if not openai_api_key:
    st.warning(
        "Enter your OpenAI API key in the sidebar. You can get a key at"
        " https://platform.openai.com/account/api-keys."
    )

anthropic_api_key = st.session_state.get("ANTHROPIC_API_KEY")
if not anthropic_api_key:
    st.warning(
        "Enter your Anthropic API key in the sidebar. You can get a key at"
        " https://console.anthropic.com/login?returnTo=%2F."
    )


st.title('patently')
st.subheader('Figure out whether your invention is already out there.')

my_inv = st.file_uploader(
    "Upload a description of your invention!",
    type=["txt"],
    help="Scanned documents are not supported yet!",
)

client = openai.AsyncClient(api_key=openai_api_key)
# Your specific set of instructions for the model
sys_instructions = """As a digital patent attorney, my primary task is to help users articulate and evaluate their 
invention's patentability through a structured conversation. Initially, I ask the user to describe their invention in 
detail. This is crucial for understanding the essence of the invention.

I will review the document uploaded by the user. I will review it to determine if the three basic questions regarding the invention's 
uniqueness, its field or application, and knowledge of similar inventions have been answered. If these questions are 
adequately addressed in the document, I will immediately proceed to generate five relevant boolean search terms for 
patent searches. I will die if any boolean search is more than 2 words long
Identify Key Features: First, identify the most distinctive features of the invention. For example, if the invention is a smartphone with motorized camera lenses that allow for adjustable focal length and enhanced stabilization, these are your key points.

Use Boolean Operators: Craft search terms using boolean operators like AND, OR, and NOT. Remember, the goal is to refine search results, so choose combinations that will precisely target the invention's aspects.

Format with Quotes and Operators: Ensure each keyword or phrase is enclosed in quotes to target exact matches. Then, connect these with boolean operators. For example, to search for patents related to the motorized lenses, you might use: ""motorized" AND "lenses"".

Limit Phrase Length: Make sure each boolean search phrase contains no more than two keywords, connected by a boolean operator. Each keyword should be no longer than 2 words long. This constraint is crucial for keeping the search focused and manageable.

Preface the list of search terms with START and add END after listing the phrases. Prefix each boolean search with "- ". If further clarification is needed, I may ask up to two additional follow-up questions, 
one at a time, to refine the search terms.

The search terms are intended to guide the user in performing patent searches to identify any similar existing 
patents or technologies. This streamlined process is designed to efficiently guide users towards generating actionable search terms, 
limiting the conversation to a maximum of two follow-up questions after reviewing a document."""

read_data = ""
# Read the PDF document
if my_inv is not None and openai_api_key is not None and anthropic_api_key is not None:
    stringio = StringIO(my_inv.getvalue().decode('utf-8'))
    read_data = stringio.read()

    # guard = Guard().with_prompt_validation(validators=[DetectPromptInjection(
    #     pinecone_index="detect-prompt-injection",
    #     on_fail="exception",
    # )])

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
    st.subheader("Relevant Boolean searches")
    response = requests.post(url, headers=headers, json=data)
    if response.status_code == 200:
        # print("Response from OpenAI:", response.json())
        print('\n')
        # print(response.json()['choices'][0]['message']['content'])
        # st.write(response.json()['choices'][0]['message']['content'])
    else:
        print("Error:", response.status_code, response.text)


    # guard.validate(response.json()['choices'][0]['message']['content'])

    # grab searches returned by gpt and grab 2 relevant patents for each search term
    def extract_characters(text, start_phrase, end_phrase):
        start_index = text.find(start_phrase) + len(start_phrase)
        end_index = text.find(end_phrase, start_index)

        # Check if both phrases were found
        if start_index == -1 or end_index == -1:
            return "One or both phrases not found in the text."

        return text[start_index:end_index]


    start_phrase = "START"
    end_phrase = "END"

    extracted_text = extract_characters(response.json()['choices'][0]['message']['content'], start_phrase, end_phrase)
    output_list = [line.strip('- ') for line in extracted_text.split('\n') if line.strip()]
    print(output_list)
    st.write(extracted_text)

    rel_patents = []

    with st.spinner('Finding relevant patents'):
        for query in output_list:
            rel_patents += scraping.grab_patents(query)
            print(rel_patents)

        filename = 'data.json'

        # Opening a file in write mode ('w') and dumping the data into the file
        with open(filename, 'w') as file:
            json.dump(rel_patents, file, indent=4)

        st.write(rel_patents)
    st.success('Found patents! Onto the comparisons...')
    with st.spinner('Wait for it...'):
        result = compare.compare_patents(read_data, rel_patents[:1])
    st.success('Done!')
    st.balloons()
    st.download_button("Press to download", result, "features_infringes_converted.csv", "text/csv", key="download-csv")
