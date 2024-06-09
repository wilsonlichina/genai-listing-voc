import base64
import streamlit as st
from pathlib import Path
import os
import json
from dotenv import load_dotenv
from llm_invoke import image_to_text, text_to_text
from amazon_scraper import get_product

# load environment variables
load_dotenv()

def generate_prompt(asin, keywords, features):
    results = get_product(asin)
    as_title = results['results'][0]['content']['title']
    as_bullet = results['results'][0]['content']['bullet_points']
    as_des = results['results'][0]['content']['description']

    user_prompt = '''
    If you were an excellent Amazon e-commerce product listing specialist.
    Please refer to the following sample of a product on Amazon: 

    <product>
    title:{title}
    bullets:{bullet}
    description:{des}
    </product>

    please refer to <product> and best seller products on amazon and product image to create product listing.
    Brand is {kw} 
    Product features are {ft} 

    please output at least 5 bullets
    In your output, I only need the actual JSON array output. Do not include any other descriptive text related to human interaction. 
    output format: 
        "title": "title",
        "bullets": "bullets",
        "description": "description"
    '''
    
    return user_prompt.format(title=as_title, bullet=as_bullet, des=as_des, kw=keywords, ft=features)


st.sidebar.header("AI Listing/VOC")
st.sidebar.write("AI Listing/VOC with Amazon Bedrock and Claude 3")

option = st.sidebar.selectbox(
    'Function Choicer',
    ('AI Listing', 'VOC'))

# title of the streamlit app
# st.title(f""":rainbow[{option} with Amazon Bedrock and Claude 3]""")

if option == 'AI Listing':
    # default listing container that houses the image upload field
    with st.container():
        # header that is shown on the web UI
        # st.subheader('Image File Upload:')
        # the image upload field, the specific ui element that allows you to upload an image
        # when an image is uploaded it saves the file to the directory, and creates a path to that image
        File = st.file_uploader('Product image', type=["png", "jpg", "jpeg"], key="new")
        
        asin = st.text_input("Amazon product ASIN", 'B0BZYCJK89')
        brand = st.text_input("Brand", 'Stanley')
        features = st.text_input("Product features")

        # this is the button that triggers the invocation of the model, processing of the image and/or question
        result = st.button("Submit")

        # this is the text box that allows the user to insert a question about the uploaded image or a question in general
        # if "product_title" not in st.session_state:
        #     st.session_state.product_title = ""
        # product_tile = st.text_input("Product Title", st.session_state.product_title)

        # if "product_bullet" not in st.session_state:
        #     st.session_state.product_bullet = ""
        # product_bullet = st.text_area("Bullet Points", st.session_state.product_bullet)

        # if "product_desc" not in st.session_state:
        #     st.session_state.product_desc = ""
        # product_desc = st.text_area("Description", st.session_state.product_desc)


        # if the button is pressed, the model is invoked, and the results are output to the front end
        if result:
            # if an image is uploaded, a file will be present, triggering the image_to_text function
            if File is not None:
                # the image is displayed to the front end for the user to see
                # st.image(File)
                # determine the path to temporarily save the image file that was uploaded
                save_folder = os.getenv("save_folder")
                print(save_folder)
                print('filename:' + File.name)

                # create a posix path of save_folder and the file name
                save_path = Path(save_folder, File.name)
                # write the uploaded image file to the save_folder you specified
                with open(save_path, mode='wb') as w:
                    w.write(File.getvalue())

                # once the save path exists...
                if save_path.exists():
                    # write a success message saying the image has been successfully saved
                    # st.success(f'Image {File.name} is successfully saved!')
                    # running the image to text task, and outputting the results to the front end
                    file_name = save_path

                    user_prompt = generate_prompt(asin, brand, features)
                    print(user_prompt)

                    output = image_to_text(file_name, user_prompt)
                    #st.write(output)

                    data = json.loads(output)
                    st.write(data['title'])

                    # #get all string from bullet points data['bullets']
                    bullet_points = ""
                    for item in data['bullets']:
                        bullet_points += "• " + item + "\n"

                    st.write(bullet_points)

                    st.write(data['description'])
                    
                    # removing the image file that was temporarily saved to perform the question and answer task
                    os.remove(save_path)

                    #st.rerun()
            # if an Image is not uploaded, but a question is, the text_to_text function is invoked
            else:
                # running a text to text task, and outputting the results to the front end
                st.write(text_to_text(''))
elif option == 'VOC':
    st.write("VOC")


