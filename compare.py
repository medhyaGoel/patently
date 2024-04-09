import anthropic
import json
import streamlit as st
import os
import pandas as pd
import openai
from dotenv import load_dotenv

load_dotenv()
anthropic_api_key = os.getenv('ANTHROPIC_API_KEY')
client_anthropic = anthropic.Anthropic(api_key=anthropic_api_key)

def compare_patents(invention, data_json):
    openai_api_key = st.session_state.get("OPENAI_API_KEY")
    client_openai = openai.OpenAI(api_key=openai_api_key)
    prompt_claim_breakdown = """
    Your task is to break down the following patent claim into the individual features.
    Output your answer into list of json objects, with each object corresponding to the independent features.
    It should have a {'feature' and 'extraction' tag.}
    The 'feature tag' should be a succinct way of labeling the feature.
    The 'extraction' should be verbatim extracted text from the patent claims to ensure accuracy.
    """

    feature_extraction_results = []

    for entry in data_json:
        id = entry["US Patent Number"]
        abstract = entry['abstract']
        claims = entry['claims']
        description = entry['description']

        custom_prompt = [prompt_claim_breakdown] + ["Here is the abstract : "] + [str(abstract)] + [
            "Here are the claims : "] + [str(claims)]
        prompt = ' '.join(custom_prompt)

        response = client_anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            system="You are a helpful patent attorney assistant.",
            messages=[
                {"role": "user",
                 "content": [{
                     "type": "text",
                     "text": prompt,
                 }]
                 }
            ]
        )

        feature_extraction = response.content[0].text
        feature_extraction_results.append(
            {"id": id, "feature_extraction": feature_extraction, "background": description})

    prompt_claim_description = """
    You will be given a json list of different features relevant to the following patent.
    You will also be given an abstract and description of the patent.
    Your goal is to provide a list of JSON objects for each of the features, keeping the 'feature' key, but now, providing a basic explanation of each feature in the 'explanation' key.
    Ideally, your explanation will be self-sufficient and not rely on other parts, so be sure to include all the relevant details.
    Also make sure you focus on the alleged novelties of this patent (i.e. what the patentee claims is a the unique/new thing).
    """

    feature_extraction_data = feature_extraction_results
    feature_explanation_results = []

    for entry in feature_extraction_data:
        id = entry["id"]
        feature_extraction = entry['feature_extraction']
        background = entry['background']
        print("\nPatent " + str(id) + ":")

        custom_prompt = [prompt_claim_description] + [
            "Here are the features and the corresponding extracted citations : "] + [str(feature_extraction)] + [
                            "Here is some background : "] + [str(background)]
        prompt = ' '.join(custom_prompt)

        response = client_anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            system="You are a helpful assistant to a patent attorney that is extremely incisive at delineating the different components of a patented invention and only outputs answers in json.",
            messages=[
                {"role": "user",
                 "content": [{
                     "type": "text",
                     "text": prompt,
                 }]
                 }
            ]
        )

        feature_explanation = response.content[0].text

        feature_explanation_results.append({"id": id, "feature_explanation": feature_explanation})
        # print(feature_explanation_results[-1])

    # Save all summaries to a single JSON file
    # feature_explanation_json = "feature_explanation.json"
    feature_explanation_data = feature_explanation_results

    # print(f"Feature-explanation saved to {feature_explanation_json}.")

    # with open(feature_explanation_json, "r") as f:
    #     feature_explanation_data = json.load(f)

    feature_infringes_results = []
    print("line 105: feature_explanation")
    for entry in feature_explanation_data:
        id = entry["id"]

        feature_explanation = entry['feature_explanation']
        print("\nPatent " + str(id) + ":")

        prompt = f"""
        I am going to give you a description of my client's invention and a list of json objects that corresponds to claim elements of a patent.
        <invention>
        {invention}
        </invention>
        <patented_features>
        {feature_explanation}
        </patented_features>
        Your task is to determine whether the invention described has each of these features. Reference the numbers, when relevant.
        Output your answer as a list of json objects, where each object correponds to each claimed feature.
        Do not start with 'Here is the analysis of the invention described in the business..' but rather start directly with the json file.
        Each feature, explicitly written, should have a 'infringes':"True"/"False"/"Unknown" value, alongside an 'explanation' key which explains in natural language your reasoning.
        Try to pick "True" or "False" when possible, and only use "Unknown" sparingly.
        Output your final answer between the <answer> tags.
        """
        #  The response should be a json file with keys "feature", "infringes", and "explanation". Do not have tabs or new line characters, but rather a direct json file.
        response = client_anthropic.messages.create(
            model="claude-3-haiku-20240307",
            max_tokens=2048,
            system="You are a helpful assistant to a patent attorney that is extremely intelligent at comparing inventions against patents, and always will format answers in a json format",
            messages=[
                {"role": "user",
                 "content": [{"type": "text",
                              "text": prompt, }]
                 }
            ]
        )

        feature_infringes = response.content[0].text
        feature_infringes_formatted = feature_infringes.split('<answer>')[1].split('</answer>')[0]
        feature_infringes_results.append({"id": id, "feature_infringes": feature_infringes_formatted})
        # feature_infringes_results.append({"id": id, "feature_infringes": feature_infringes})
        print(feature_infringes_results[-1])

    # Save all summaries to a single JSON file
    feature_infringes_json = "feature_infringes.json"
    with open(feature_infringes_json, 'w') as jsonfile:
        json.dump(feature_infringes_results, jsonfile, indent=4)
    # feature_infringes_data = feature_infringes_results
    # Provided JSON-like text
    json_like_string = feature_infringes_results[0]['feature_infringes']

    try:
        json_data = json.loads(json_like_string)
    except json.JSONDecodeError as e:
        print(f"Error decoding JSON: {e}")
        json_data = None

    # If json_data is successfully parsed, write it to a file
    if json_data is not None:
        # Define the file path where the JSON data will be saved
        json_file_path = 'output.json'

        # Write the JSON data to a file
        with open(json_file_path, 'w') as json_file:
            json.dump(json_data, json_file, indent=4)

        print(f"Data has been written to {json_file_path}")

    with open(feature_infringes_json, 'r') as file:
        data = json.load(file)

    # Prepare a list to hold all features and their details
    features_list = []

    # Iterate over the entries to parse the 'feature_infringes' field and extract the data
    for entry in data:
        # Extract each feature and its details
        feature_info = json.loads(entry['feature_infringes'])
        for fi in feature_info:
            # Append a new dictionary with the required fields to the list
            features_list.append({
                'us_patent_number': entry['id'],
                'feature': fi['feature'],
                'infringes': fi['infringes'],
                'explanation': fi['explanation']
            })
            print(len(features_list))

    # Create a DataFrame from the list of features
    features_df = pd.DataFrame(features_list)

    # Convert DataFrame to CSV
    csv_file_path_2 = 'feature_infringes_converted.csv'
    features_df.to_csv(csv_file_path_2, index=False)
    return features_df.to_csv().encode('utf-8')
