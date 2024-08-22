import streamlit as st
from langchain.chat_models.openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from langchain.pydantic_v1 import BaseModel, Field
import re
from typing import Dict
import json
import os
# from dotenv import load_dotenv
from streamlit_extras.switch_page_button import switch_page

if 'openai_key' not in st.session_state:
    st.session_state.openai_key = ""
    
# Ensure you have set your OpenAI API key in your environment variables
# load_dotenv()
# os.environ["OPENAI_API_KEY"] = os.getenv("OPENAI_API_KEY")

st.set_page_config(initial_sidebar_state="collapsed")

api_key = st.text_input("Enter your OpenAI API key:", type="password")

if api_key:
    st.session_state.openai_key=api_key
st.markdown(
    """
<style>
    [data-testid="collapsedControl"] {
        display: none
    }
</style>
""",
    unsafe_allow_html=True,
)

class ChatbotResponse(BaseModel):
    response: str = Field(description="The AI's response to the user")
    collected_data: Dict[str, str] = Field(default_factory=dict, description="Collected information from the user")
    isCompleted: bool = Field(default=False, description="Whether all required information has been collected")

parser = PydanticOutputParser(pydantic_object=ChatbotResponse)

chatbot_prompt = ChatPromptTemplate.from_template(
    """
    <system>
    You are an AI assistant designed to gather essential company-level information for Product Requirements Document (PRD) generation. Your task is to collect the requireid information from the user:
   
    
    <requireid_info>
    1. Company name and brief description
    2. Brand guidelines (tone, style)
    3. Target market segments
    4. Standard development methodology
    5. Company-wide tech stack
    6. General approval and review processes
    7. Key compliance and security standards
    8. Integration requirements with existing systems
    </required_info>

    Instructions:
    1. If this is the start of the conversation, introduce yourself and explain your purpose.
    2. If an answer is unclear or incomplete, ask for clarification before moving on.
    3. If you already have that information do not ask questions about it
    5. When all required information is gathered isCompleted=true and  make the summarize of the collected data and inform the user that the information gathering is complete.
    6. Do not ask questions if you have some information about a required subject
    Remember to be polite, patient, and helpful throughout the conversation. If the user asks questions or needs explanations about any of the items, provide clear and concise information to assist them.
    </system>


    Current conversation history:
    {history}

    Current collected data:
    {collected_data}


    Human: {human_input}

    AI: Respond politely and ask the next relevant question. Your response must be in this JSON format:
    {format_instructions}

    Ensure that your response includes the following fields:
    - 'response': Your actual response to the human, including the next question you're asking or the confirmation of information received.
    - 'collected_data': A dictionary of the information collected so far, with keys corresponding to the items in the list above.
    - 'isCompleted': A boolean indicating whether all information f has been collected (true) or if there are still items to address (false).
    """
)


def parse_ai_response(response_content):
    try:
        # First, try to parse the entire response as JSON
        parsed_json = json.loads(response_content)
        return ChatbotResponse(**parsed_json)
    except json.JSONDecodeError:
        # If that fails, try to extract JSON from the response
        json_match = re.search(r'\{.*\}', response_content, re.DOTALL)
        if json_match:
            try:
                parsed_json = json.loads(json_match.group())
                return ChatbotResponse(**parsed_json)
            except json.JSONDecodeError:
                pass  # If this fails, fall through to the manual parsing

        # If JSON extraction fails, manually parse the response
        response = response_content
        collected_data = {}
        is_completed = False

        # Try to extract collected data
        data_start = response_content.find("Collected Data:")
        if data_start != -1:
            data_section = response_content[data_start:]
            data_items = re.findall(r'- (.*?): (.*?)(?:\n|$)', data_section)
            collected_data = dict(data_items)

        # Check if information gathering is completed
        if "Information gathering completed: Yes" in response_content:
            is_completed = True

        return ChatbotResponse(
            response=response,
            collected_data=collected_data,
            isCompleted=is_completed
        )

def handle_submit():
    if st.session_state.user_input and st.session_state.user_input.strip():
        user_input = st.session_state.user_input
        
        # Prepare the prompt
        prompt = chatbot_prompt.format_prompt(
            history=st.session_state.history,
            collected_data=st.session_state.collected_data,
            human_input=user_input,
            format_instructions=parser.get_format_instructions()
        )
        openai_key = st.session_state.openai_key
        chat_model = ChatOpenAI(temperature=0.5, model="gpt-4o-2024-08-06",api_key=openai_key)
        
        # Get the response from the language model
        response = chat_model(prompt.to_messages())

        # Parse the response
        parsed_response = parse_ai_response(response.content)

        # Update the collected data and current item
        st.session_state.collected_data = parsed_response.collected_data
       

        # Add to history
        st.session_state.history.append({"role": "human", "content": user_input})
        st.session_state.history.append({
            "role": "ai", 
            "content": parsed_response.response,
            "collected_data": parsed_response.collected_data,
            "isCompleted": parsed_response.isCompleted
        })

        # Check if all information has been collected
        if parsed_response.isCompleted:
            st.session_state.conversation_active = False

        # Clear the input box
        st.session_state.user_input = ""

# Streamlit app
if  st.session_state.openai_key:
    st.title("PRD Information Gathering Chatbot")

# Initialize session state
if 'history' not in st.session_state:
    st.session_state.history = []
if 'collected_data' not in st.session_state:
    st.session_state.collected_data = {}
if 'conversation_active' not in st.session_state:
    st.session_state.conversation_active = True
if 'user_input' not in st.session_state:
    st.session_state.user_input = ""


# Display chat history
for i, message in enumerate(st.session_state.history):
    if message["role"] == "human":
        st.text_area("You:", value=message["content"], height=50, key=f"human_message_{i}", disabled=True)
    elif message["role"] == "ai":
        st.markdown(f"**AI:** {message['content']}")
        
        # Check if 'collected_data' is present in the message
        if 'collected_data' in message:
            st.markdown("**Collected Data:**")
            for key, value in message['collected_data'].items():
                st.markdown(f"- {key}: {value}")
        
        # Check if 'isCompleted' is present in the message
        if 'isCompleted' in message:
            st.markdown(f"**Information gathering completed:** {'Yes' if message['isCompleted'] else 'No'}")
        
        st.markdown("---")  # Ad
        

# User input form
if st.session_state.openai_key:
    with st.form(key='user_input_form'):
        user_input = st.text_input("Your message:", key="user_input", disabled=not st.session_state.conversation_active)
        submit_button = st.form_submit_button(label='Send', on_click=handle_submit)

# Check if all information has been collected
if not st.session_state.conversation_active:
    st.success("All required information has been collected!")
    st.write("Here's a summary of the collected information:")
    for key, value in st.session_state.collected_data.items():
        st.write(f"**{key}:** {value}")
    if st.button("Start Interaction", type='primary'):
        switch_page("conversation")

