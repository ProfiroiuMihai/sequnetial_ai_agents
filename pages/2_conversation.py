from openai import OpenAI
import os
import streamlit as st
from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain.chains.llm import LLMChain
from langchain_openai import ChatOpenAI
from streamlit_extras.switch_page_button import switch_page

st.set_page_config(initial_sidebar_state="collapsed")

if 'openai_key' not in st.session_state:
    st.session_state.openai_key = ""
    
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
st.title("PRD Communicate with chat:")
history=st.session_state.get('history')


system_prompt_template = """
You are an AI assistant specialized in product management. Your primary role is to help users create detailed Product Requirements Documents (PRDs) and assist with various product management tasks. You should be knowledgeable about product development processes, market analysis, and user experience design.
Core Responsibilities:

Create and refine Product Requirements Documents (PRDs)
Assist with feature ideation and prioritization
Help define user personas and user stories
Provide insights on market trends and competitive analysis
Offer guidance on product strategy and roadmap planning

Interaction Style:

Be professional yet friendly in your communication
Ask clarifying questions when needed to gather all necessary information
Provide structured, detailed responses
Offer to elaborate on any point if the user needs more information
Be proactive in suggesting additional considerations or potential issues

PRD Creation Process:

When a user presents a product idea, ask for key details such as:

Primary target users
Business goals
Key features or functions


Based on the provided information, and the collected_info from the company draft a comprehensive PRD including:

Executive summary (tl;dr)
Goals (business and user goals)
Non-goals
User stories
User experience description
Narrative
Success metrics
Technical considerations
Milestones and sequencing


Additional Guidelines:

Always consider user needs, market demands, and business objectives in your recommendations
Encourage users to think about potential challenges and how to address them
Suggest ways to validate assumptions and gather user feedback
Be prepared to iterate on ideas and documents based on user input
Offer to break down complex tasks into manageable steps if needed

Remember, your goal is to help users develop well-defined, user-centric products that align with business objectives. Adapt your responses to the user's level of expertise and the specific needs of their project.
"""

# Define the human prompt template
human_prompt_template = """
You’re engaging with an AI assistant focused on product management. This assistant is here to help you craft Product Requirements Documents (PRDs), brainstorm features, define user stories, and offer strategic product insights.

To maximize the assistant’s effectiveness:

Be Clear and Concise: Share specific details about your product idea or the task you need assistance with.
Prepare for Follow-ups: The assistant may ask additional questions to gather more context or details.
Ask for Clarifications: Feel free to request explanations or more depth on any point.
Request Revisions: Don’t hesitate to ask for adjustments or iterations on PRDs or other outputs.
Explore Various Aspects: Use the assistant to dive into target users, business objectives, and essential features.


Here’s some brief information about the company:
<company_info>
{collected_info}
</company_info>


Chat History between PM and ai assistant is:
<chat_history>
{chat_history}
</chat_history>

Now, please answer the user's question:
<user_instructions>
{user_input}
</user_instructions>
"""

system_prompt = PromptTemplate(template=system_prompt_template, input_variables=[])
human_prompt = PromptTemplate(template=human_prompt_template, input_variables=["user_input","collected_info","chat_history"])
ChatPromptTemplate.from_messages(
    [
        
    ]
)
# Initialize the language model (you can choose your model and configuration)
openai_llm = ChatOpenAI(
    model="gpt-4o-2024-08-06",
    temperature=0.5,
    api_key= st.session_state.openai_key,
    streaming=True
)
# Create LLMChain for the system prompt
system_llm_chain = LLMChain(prompt=system_prompt, llm=openai_llm)

# Create LLMChain for the human prompt
human_llm_chain = LLMChain(prompt=human_prompt, llm=openai_llm,verbose=True,)

def warningMarkdown():
    st.warning(f"**Information Collection Not Completed please go back")
    if st.button("Go Back", type='primary'):
        switch_page("app")

def handle_submit():
    if st.session_state.user_input:
        user_input = st.session_state.user_input
        st.session_state.conversation.append({
            "role": "user", 
            "content": user_input,
        })
        with st.chat_message("user"):
            st.markdown(user_input)
        # First run the system prompt to establish context
        # system_response = system_llm_chain.run()
        collectedData= history[len(history)-1]
        
        # Then run the human prompt with user input
        response = human_llm_chain.run(user_input=user_input,collected_info=collectedData['collected_data'],chat_history=st.session_state.conversation)
       
        st.session_state.conversation.append({
            "role": "assistant", 
            "content": response,
        })
        with st.chat_message("assistant"):
            st.write(response)
        # st.session_state.user_input = ""
        st.components.v1.html(scroll_to_bottom_script)
        return response
        
def startConveration():
    # User input form
    # with st.form(key='user_input_form'):
    #     user_input = st.text_input("Ask your query to Chat PRD:", key="user_input")
    #     submit_button = st.form_submit_button(label='Send', on_click=handle_submit)
    if prompt :=st.chat_input("Ask your query to Chat PRD:", key="user_input"):
        handle_submit()
        
        
 
if 'conversation' not in st.session_state:
    st.session_state.conversation = []       


scroll_to_bottom_script = """
<script>
window.scrollTo(0, document.body.scrollHeight);
</script>
"""

# Display chat history
for i, message in enumerate(st.session_state.conversation):
     with st.chat_message(message['role']):
        st.markdown(message['content'])
        st.markdown("---")  # Ad

if history:
    
    collectedData= history[len(history)-1]
    print(collectedData['collected_data'])
    if 'isCompleted' in collectedData:
        if(collectedData['isCompleted']):
            startConveration()
        else:
            warningMarkdown()   
    else:
        warningMarkdown()    
else:
    warningMarkdown()            
    
