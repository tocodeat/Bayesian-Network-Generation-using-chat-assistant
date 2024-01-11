from typing import Union, List, Dict
import re
import os

from langchain.agents import initialize_agent
from langchain.memory import ConversationBufferMemory
from langchain.chat_models import ChatOpenAI
from langchain.agents import AgentType
from langchain.schema import AgentAction, AgentFinish, OutputParserException
from langchain.agents import AgentOutputParser, AgentExecutor

class CustomOutputParser(AgentOutputParser):

    def parse(self, llm_output: str) -> Union[AgentAction, AgentFinish]:
        # Check if agent should finish
        if 'Final Answer:' in llm_output:
            return AgentFinish(
                # Return values is generally always a dictionary with a single `output` key
                # It is not recommended to try anything else at the moment :)
                return_values={'output': llm_output.split('Final Answer:')[-1].strip()},
                log=llm_output,
            )
        # Parse out the action and action input
        regex = r'Action\s*\d*\s*:(.*?)\nAction\s*\d*\s*Input\s*\d*\s*:[\s]*(.*)'
        match = re.search(regex, llm_output, re.DOTALL)
        if not match:
            raise OutputParserException(f"Could not parse LLM output: `{llm_output}`")
        action = match.group(1).strip()
        action_input = match.group(2)
        # Return the action and action input
        return AgentAction(tool=action, tool_input=action_input.strip(' ').strip('"'), log=llm_output)
    
def create_agent(api_key: str) -> AgentExecutor:
    
    # Initialize the LangChain agent
    memory = ConversationBufferMemory(memory_key='chat_history', return_messages=True)
    llm = ChatOpenAI(openai_api_key=api_key, temperature=0, streaming=False)

    agent_executor = initialize_agent(
        tools=[],  # Define tools if needed
        llm=llm,
        agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
        verbose=True,
        memory=memory,
        output_parser=CustomOutputParser(),
        return_intermediate_steps=False,
        handle_parsing_errors=True
    )
    
    return agent_executor

def save_conversation_history(path: str, activity_code: str, conversation: List[Dict[str, str]]) -> None:
    """
    Save the conversation history to a text file
    
    Parameters
    ----------
    path : str
        The path to the directory where the conversation history should be saved.
    activity_code : str
        The activity code
    conversation : List[Dict[str, str]]
        The conversation history, a list of dictionaries with keys `user` and `bot`.
        
    Returns
    -------
    None 
    """
    conversation_file = os.path.join(path, f'conversation_{activity_code}.txt')
    with open(conversation_file, 'w') as file:
        for entry in conversation:
            file.write(f"User: {entry['user']}\n")
            file.write(f"Bot: {entry['bot']}\n")
            file.write("\n")
            
def initial_prompt(activity_name: str) -> str:
    """
    Generate the initial prompt for the LangChain agent
    
    Parameters
    ----------
    activity_name : str
        The name of the activity
        
    Returns
    -------
    str
        The initial prompt
    """
    initial_prompt = f"""
    I want you to help me elicit following variables about the activity, {activity_name}, from the human project managers through conversation. Note that you are very thoughtful and kind assistant. You should 
    answer any question if human ask even it is not relevant, then go back to eliciting the information. 

    Here are few hard rules to follow:
        - The human will first start with a random prompt. You should accept any input from human initially and then start asking the relevant questions.
        - You need to ask enough questions to gather all the information and double checked with human that the received information is correct.
        - For any duration related variables, human's response must be in weeks (numeric value or range of values). If human answered in days or months of period, ask again for duration in weeks.
        - For any resource related variables, human's response must be single value of three resource factors: Technology, People, and Cost. If human answered with multiple values, ask again for single value.
        
    Here are variables followed by sample questions:
        1) Most_Likely_Duration
            - Q: 'How long do you think the {activity_name} activity will most likely take?'
        2) Minimum_Duration
            - Q: 'What's the shortest time you estimate to complete the {activity_name} activity?'
        3) Maximum_Duration
            - Q: 'What's the longest time you estimate to complete the {activity_name} activity?'
        4) Most_Valued_Resource
            - Q: 'Among the three resource factors: Technology, People, and Cost, which one holds the highest value in completing the {activity_name} activity?'
        5) Least_Valued_Resource
            - Q: 'Among the three resource factors: Technology, People, and Cost, which one has the least significance in completing the {activity_name} activity?'
        6) Resource_Impact_Bin_1
            - Q: 'If 0 - 25% of the resource is allocated to the {activity_name} activity, which one of the durations (Most Likely, Minimum, Maximum) will more likely to be observed in reality?'
        7) Resource_Impact_Bin_2
            - Q: 'If 25 - 50% of the resource is allocated to the {activity_name} activity, which one of the durations (Most Likely, Minimum, Maximum) will more likely to be observed in reality?'
        8) Resource_Impact_Bin_3
            - Q: 'If 50 - 75% of the resource is allocated to the {activity_name} activity, which one of the durations (Most Likely, Minimum, Maximum) will more likely to be observed in reality?'
        9) Resource_Impact_Bin_4
            - Q: 'If 75 - 100% of the resource is allocated to the {activity_name} activity, which one of the durations (Most Likely, Minimum, Maximum) will more likely to be observed in reality?'
            
    This prompt only provides the context, so do not respond this this prompt. You should start asking the questions to the human project manager right away.
    """
    
    return initial_prompt