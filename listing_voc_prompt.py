import os
import boto3
import json
from dotenv import load_dotenv

import base64
import io
from PIL import Image

from langchain.agents import tool 
from langchain_community.chat_models import BedrockChat
from langchain.llms import Bedrock

from amazon_scraper import get_product, get_reviews, get_bestsellers

# loading in variables from .env file
load_dotenv()

# instantiating the Bedrock client, and passing in the CLI profile
boto3.setup_default_session(profile_name=os.getenv("profile_name"))
bedrock = boto3.client('bedrock-runtime', 'us-east-1', endpoint_url='https://bedrock-runtime.us-east-1.amazonaws.com')

def gen_listing_prompt(asin, domain, keywords, features, language):
    results = get_product(asin, domain)
    as_title = results['results'][0]['content']['title']
    as_bullet = results['results'][0]['content']['bullet_points']
    as_des = results['results'][0]['content']['description']
    

    systemrole = '''If you were an excellent Amazon product listing specialist.
    Your task is to create compelling and optimized product listings for Amazon based on the provided information.
    Please refer to the following examples and best seller products on Amazon to create a comprehensive product listing.
    
    Example of a good product listing on Amazon:

    <Example>
        <title>{title}</title>
        <bullets>{bullet}</title>
        <description>{des}</description>
    </Example>

    Please translate the result into {lang}
    '''

    prompt_template = '''Please refer to the above image and the following production infomation fo to create product listing.

    Product Information:

    <product_information>
        <brand>{kw}</brand> 
        <keywords>{ft}</keywords> 
    </product_information>

    Please output at least 5 bullets and translate the result into {lang}

    In your output, I only need the actual JSON array output. Do not include any other descriptive text related to human interaction. 
    the key of json: "title", "bullets", description".
    '''

    system_prompt = systemrole.format(title=as_title, bullet=as_bullet, des=as_des,lang=language)
    user_prompt  =prompt_template.format(kw=keywords, ft=features,lang=language)

    return system_prompt, user_prompt


def gen_voc_prompt(asin, domain, language):
    print('asin:' + asin, 'domain:' + domain)
    results = get_reviews(asin, domain)

    system_role = '''
    You are an analyst tasked with analyzing the provided customer review examples on an e-commerce platform and summarizing them into a comprehensive Voice of Customer (VoC) report. Your job is to carefully read through the product description and reviews, identify key areas of concern, praise, and dissatisfaction regarding the product. You will then synthesize these findings into a well-structured report that highlights the main points for the product team and management to consider.

    The report should include the following sections:
    Executive Summary - Briefly summarize the key findings and recommendations
    Positive Feedback - List the main aspects that customers praised about the product
    Areas for Improvement - Summarize the key areas of dissatisfaction and improvement needs raised by customers
    Differentiation from Competitors - Unique features or advantages that set a product apart from competitors
    Unperceived Product Features - Valuable product characteristics or benefits that customers are not fully aware of
    Core Factors for Repurchase and Recommendation - Critical elements that drive customers to repurchase and recommend a product
    Sentiment Analysis - Analyze the sentiment tendencies (positive, negative, neutral) in the reviews
    Topic Categorization - Categorize the review content by topics such as product quality, scent, effectiveness, etc.
    Recommendations - Based on the analysis, provide recommendations for product improvements and marketing strategies

    When writing the report, use concise and professional language, highlight key points, and provide reviews examples where relevant. Also, be mindful of protecting individual privacy by not disclosing any personally identifiable information.

    Please translate the result into {lang}
    '''

    prompt_template = '''<Product descriptions>
    {product_description}
    <Product descriptions>

    <product reviews>
    {product_reviews}
    <product reviews>

     Please translate the result into {lang}
    '''
    system_prompt = system_role.format(lang=language)
    user_prompt  = prompt_template.format(product_description='', product_reviews=results['results'], lang=language)

    return system_prompt, user_prompt

def image_base64_encoder(image_name):
    """
    This function takes in a string that represent the path to the image that has been uploaded by the user and the function
    is used to encode the image to base64. The base64 string is then returned.
    :param image_name: This is the path to the image file that the user has uploaded.
    :return: A base64 string of the image that was uploaded.
    """
    # opening the image file that was uploaded by the user
    open_image = Image.open(image_name)
    # creating a BytesIO object to store the image in memory
    image_bytes = io.BytesIO()
    # saving the image to the BytesIO object
    open_image.save(image_bytes, format=open_image.format)
    # converting the BytesIO object to a base64 string and returning it
    image_bytes = image_bytes.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    # getting the appropriate file type as claude 3 expects the file type to be presented
    file_type = f"image/{open_image.format.lower()}"
    # returning both the formatted file type string, along with the base64 encoded image
    return file_type, image_base64


def image_to_text(image_name, sysprompt, text) -> str:
    """
    This function is used to perform an image to text llm invocation against Claude 3. It can work with just an image and/or with
    text. If the user does not use any text, a default prompt will be passed in along with the system prompt as Claude 3 expects
    text in the text block of the prompt.
    :param image_name: This is the path to the image file that the user has uploaded.
    :param text: This is the text the user inserted in the text box on the frontend.
    :return: A natural language response giving a detailed analysis of the image that was uploaded or answering a specific
    question that the user asked along with the image.
    """
    # invoking the image_base64_encoder function to encode the image to base64 and get the file type string
    file_type, image_base64 = image_base64_encoder(image_name)
    # the system prompt is used as a default prompt, and is always passed into to the model
    # TODO: Edit the system prompt based on your specific use case
    system_prompt = """Describe every detail you can about this image, be extremely thorough and detail even the most minute aspects of the image. 
    
    If a more specific question is presented by the user, make sure to prioritize that answer.
    """

    if sysprompt != "":
        system_prompt = sysprompt

    # checking if the user inserted any text along with the image, if not, we set text to a default since claude expects
    # text in the text block of the prompt.
    if text == "":
        text = "Use the system prompt"
    # this is the primary prompt passed into Claude3 with the system prompt, user uploaded image in base64 and any
    # text the user inserted
    prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.9,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": file_type,
                            "data": image_base64
                        }
                    },
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
    }
    # formatting the prompt as a json string
    json_prompt = json.dumps(prompt)
    # invoking Claude3, passing in our prompt
    response = bedrock.invoke_model(body=json_prompt, modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                                    accept="application/json", contentType="application/json")
    # getting the response from Claude3 and parsing it to return to the end user
    response_body = json.loads(response.get('body').read())
    # the final string returned to the end user
    llm_output = response_body['content'][0]['text']
    # returning the final string to the end user
    return llm_output


def text_to_text(sysprompt, text):
    """
    This function is used if a user does not upload an image, and only uploads text, this text is directly passed into
    Claude3.
    :param text: This is the text that the user inserts on the frontend.
    :return: A natural language response to the question that the user inserted on the frontend.
    """
    # the system prompt is used as a default prompt, and is always passed into to the model
    # TODO: Edit the system prompt based on your specific use case
    system_prompt = """Answer every aspect of the provided question as thoroughly as possible. Be extremely thorough and provide detailed answers to the user provided question.
    """

    if sysprompt != "":
        system_prompt = sysprompt

    # this is the formatted prompt that contains both the system_prompt along with the text prompt that was inserted by the user.
    prompt = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 2048,
        "temperature": 0.5,
        "system": system_prompt,
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": text
                    }
                ]
            }
        ]
    }
    # formatting the prompt as a json string
    json_prompt = json.dumps(prompt)
    # invoking Claude3, passing in our prompt
    response = bedrock.invoke_model(body=json_prompt, modelId="anthropic.claude-3-sonnet-20240229-v1:0",
                                    accept="application/json", contentType="application/json")
    # getting the response from Claude3 and parsing it to return to the end user
    response_body = json.loads(response.get('body').read())
    # the final string returned to the end user
    llm_output = response_body['content'][0]['text']
    # returning the final string to the end user
    return llm_output

