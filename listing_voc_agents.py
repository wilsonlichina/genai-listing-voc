import os
import boto3
import json
from dotenv import load_dotenv

import base64
import io
import base64
from pathlib import Path

#from langchain_community.chat_models import BedrockChat
from langchain_aws import ChatBedrock
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.messages import (SystemMessage, HumanMessage, AIMessage)
from langchain.agents import AgentExecutor, AgentType, create_tool_calling_agent, tool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.messages import HumanMessage

from amazon_scraper import get_product, get_reviews

def initialize_llm():
    """Initialize the Bedrock runtime."""
    bedrock_runtime =  boto3.client(
        service_name="bedrock-runtime",
        region_name="us-east-1",
    )

    """Initialize the language model."""
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    model_kwargs = {
        "max_tokens": 8192,
        "temperature": 0.0,
        "top_k": 250,
        "top_p": 1
    }

    # genertate Bedrock by langchain
    llm = ChatBedrock(
        client = bedrock_runtime,
        model_id = model_id,
        model_kwargs = model_kwargs,
    )

    return llm

bedrock_llm = initialize_llm()
save_folder = os.getenv("save_folder")


def invoke_sample():
    messages = [
        ("system", "You are a helpful assistant."),
        ("human", "{question}"),
    ]

    prompt = ChatPromptTemplate.from_messages(messages)

    chain = prompt | bedrock_llm | StrOutputParser()

    # Chain Invoke
    response = chain.invoke({"question": "tell me a joke"})
    print(response)

def stream_sample():
    # Stream - Example 1
    system_message = "You are a helpful assistant that translates {input_language} to {output_language}."
    human_message = "{text}"

    messages = [
        ("system", system_message),
        ("human", human_message)
    ]

    prompt = ChatPromptTemplate.from_messages(messages)

    chain = prompt | bedrock_llm | StrOutputParser()

    for chunk in chain.stream(
        {
            "input_language": "English",
            "output_language": "Korean",
            "text": "I love Korean BBQ",
        }
    ):
        print(chunk, end="", flush=True)

    # Stream - Example 2
    messages = [
        ("human", "Give me a list of famous tourist attractions in Seoul, Korea")
    ]

    prompt = ChatPromptTemplate.from_messages(messages)

    chain = prompt | bedrock_llm | StrOutputParser()

    for chunk in chain.stream({}):
        print(chunk, end="", flush=True)


def multimodal_single_image():
    img1_path = Path(save_folder, "515SFP7ai3L._AC_SL1500_.jpg")
    img1_base64 = base64.b64encode(img1_path.read_bytes()).decode("utf-8")

    messages = [
        HumanMessage(
            content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img1_base64}",
                    },
                },
                {
                    "type": "text",
                    "text": "What's in this image?"
                },
            ]
        )
    ]

    for chunk in bedrock_llm.stream(messages):
        print(chunk.content, end="", flush=True)

def multimodal_multiple_images():
    img1_path = Path(save_folder, "515SFP7ai3L._AC_SL1500_.jpg")
    img1_base64 = base64.b64encode(img1_path.read_bytes()).decode("utf-8")

    img2_path = Path(save_folder, "61KePAu1JAL._AC_SL1500_.jpg")
    img2_base64 = base64.b64encode(img2_path.read_bytes()).decode("utf-8")

    messages = [
        HumanMessage(
            content = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img1_base64}",
                    },
                },
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img2_base64}",
                    },
                },
                {   
                    "type": "text",
                    "text": "Compare two images"
                },
            ]
        )
    ]

    for chunk in bedrock_llm.stream(messages):
        print(chunk.content, end="", flush=True)

@tool
def get_product_info(asin):
    """
    Get product information from Amazon.

    Args:
        asin (str): The ASIN of the product.

    Returns:
        str: The product information.

    """
    product = get_product(asin, 'com')
    return product

@tool
def magic_function(input: int) -> int:
    """Applies a magic function to an input."""
    return input + 2      

search = TavilySearchResults()

def test():
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a helpful assistant"),
                ("placeholder", "{chat_history}"),
                ("human", "{input}"),
                ("placeholder", "{agent_scratchpad}"),
            ]
        )

        tools = [magic_function]

        agent = create_tool_calling_agent(bedrock_llm, tools, prompt)
        agent_executor = AgentExecutor(agent=agent, tools=tools, verbose=True)

        agent_executor.invoke({"input": "what is the value of magic_function(3)?"})

def create_listing(asin:str, image_name:str, brand:str, product_features:str):
    print(f"asin: {asin}")
    img1_path = Path(save_folder, image_name)
    img1_base64 = base64.b64encode(img1_path.read_bytes()).decode("utf-8")

    system_message = "You are a amazon product speciallist"
    human_message = [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{img1_base64}",
                    },
                },
                {   
                    "type": "text",
                    "text": "{input}"
                },
            ]

    prompt = ChatPromptTemplate.from_messages(
            [
                ("system", "You are a amazon product specaillist. please use search tool get infomation"),
                ("human", human_message),
                ("placeholder", "{agent_scratchpad}"),
            ]
    )   

    tools = [search, get_product_info]

    agent = create_tool_calling_agent(bedrock_llm, tools, prompt)
    
    agent_executor = AgentExecutor(agent=agent, 
                                   tools=tools, 
                                   verbose=True)
    
    input = f'''please create a good product listing for image. you can refer to the product list of amazon asin {asin}
    the brand is {brand}. the product description should highlight {product_features}
    In your output, I only need the actual JSON array output. Do not include any other descriptive text related to human interaction. 
    output format: 
    {'{'}
        "title": "title", 
        "bullets": "bullets", 
        "description": "description"
    {'}'}'''
    
    #input = f'''please create a good product listing and output json for amazon asin {asin}'''
    #print(input)
    
    return agent_executor.invoke({"input": input})

# create_listing("B0BZYCJK89", "61KePAu1JAL._AC_SL1500_.jpg", "", "")
# test()