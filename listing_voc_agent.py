import os
import boto3
import base64
import io

from PIL import Image

from langchain.agents import tool 
from langchain_community.chat_models import BedrockChat
from langchain.llms import Bedrock

from amazon_scraper import get_product, get_reviews

from crewai import Agent, Task, Crew
from crewai.telemetry import Telemetry

#Disable CrewAI Anonymous Telemetry
def noop(*args, **kwargs):
    pass

for attr in dir(Telemetry):
    if callable(getattr(Telemetry, attr)) and not attr.startswith("__"):
        setattr(Telemetry, attr, noop)

#Config Amazon Bedrock claude3
def initialize_llm():
    """
    Initialize a Large Language Model (LLM) instance using the Bedrock Runtime service.

    Returns:
        BedrockChat: An instance of the BedrockChat class, which represents the initialized LLM.

    """
    model_id = "anthropic.claude-3-sonnet-20240229-v1:0"
    model_kwargs = {
        "max_tokens": 8192,
        "temperature": 0.0,
        "top_k": 250,
        "top_p": 1,
        "stop_sequences": ["\n\nHuman"],
    }

    # Check if AWS_REGION environment variable is set
    aws_region = os.environ.get("AWS_REGION", "us-east-1")

    bedrock_runtime = boto3.client(
        service_name="bedrock-runtime",
        region_name=aws_region,
    )

    bedrock_llm = BedrockChat(
        client=bedrock_runtime,
        model_id=model_id,
        model_kwargs=model_kwargs,
    )

    return bedrock_llm

bedrock_llm = initialize_llm()

def image_base64_encoder(image_name):
    """
    This function takes in a string that represent the path to the image that has been uploaded by the user and the function
    is used to encode the image to base64. The base64 string is then returned.
    :param image_name: This is the path to the image file that the user has uploaded.
    :return: A base64 string of the image that was uploaded.
    """

    open_image = Image.open(image_name)
    image_bytes = io.BytesIO()
    open_image.save(image_bytes, format=open_image.format)
    image_bytes = image_bytes.getvalue()
    image_base64 = base64.b64encode(image_bytes).decode('utf-8')
    file_type = f"image/{open_image.format.lower()}"

    return file_type, image_base64

@tool
def get_product_info(asin):
    """
    Get product information from Amazon.

    Args:
        asin (str): The ASIN of the product.

    Returns:
        str: The product information.

    """
    product_info = get_product(asin, 'com')
    return product_info

@tool
def get_product_reviews(asin, domain):
    """
    Get product reviews from Amazon.

    Args:
        asin (str): The ASIN of the product.

    Returns:
        str: The product reviews.

    """
    product_reviews = get_reviews(asin, 'com')


product_loader = Agent(
    role='Amazon product infomation scrapper',
    goal='If user input amazon ASIN, you load production information by ASIN',
    backstory='create product listing or amazon reviews documents',
    verbose=True,
    tools=[get_product_info],
    allow_delegation=False,
    llm=bedrock_llm,
    memory=True,
)

listing_specialist = Agent(
  role='Amazon Listing Specialist',
  goal='To increase search visibility and attract users, create outstanding listings.',
  backstory='''please refer to product image to create product listing.
  In your output, I only need the actual JSON array output. Do not include any other descriptive text related to human interaction. 
  output format: 
    "title": "title",
    "bullets": "bullets",
    "description": "description"
    ''',
  verbose=True,
  allow_delegation=True,
  llm=bedrock_llm
)

def init_crew(asin:str, domain:str, image_name:str, brand:str, product_features:str):
    product_loading_task = Task(
        description=f"""asin: {asin} ,domain:{domain}""",
        agent=product_loader,
        expected_output='''The actual JSON array output. Do not include any other descriptive text related to human interaction.'''
    )

    file_type, image_base64 = image_base64_encoder(image_name)

    listing_creation_task = Task(
        description=f"""For the product image with {file_type} format and base64 encoding {image_base64}, please refer to the information from the listing specialist agents to create the product listing. 
        The product listing title should include the brand name {brand}. Additionally, the product features should highlight {product_features}.
        Please be sure to not simply copy from the reference Amazon ASIN {asin} product listing.
        """,
        agent=listing_specialist,
        expected_output=f'The actual JSON array output. Do not include any other descriptive text related to human interaction.'
    )

    crew = Crew(
        agents = [product_loader, listing_specialist],
        tasks = [product_loading_task, listing_creation_task],
        verbose = 2, 
    )
    return crew

def main(asin, domain, image_name, brand, product_features):
    """
    This function calls the kickoff function with the provided app name and a rank of -1 (for all reviews).
    It prints the result returned by the kickoff function.
    """
    file_type, image_base64 = image_base64_encoder(image_name)
    app_crew = init_crew(asin, domain, image_name, brand, product_features)
    result = app_crew.kickoff()
    print(result)


#main('B0BZYCJK89', 'com', '', 'Stanley', '')