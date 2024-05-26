import streamlit as st
from pathlib import Path
import os
import json
from dotenv import load_dotenv
from llm_invoke import image_to_text, text_to_text

# load environment variables
load_dotenv()

st.sidebar.header("AI Listing/VOC")
st.sidebar.write("AI Listing/VOC with Amazon Bedrock and Claude 3")

option = st.sidebar.selectbox(
    'Function Choicer',
    ('AI Listing', 'VOC'))

# title of the streamlit app
st.title(f""":rainbow[{option} with Amazon Bedrock and Claude 3]""")

# default container that houses the image upload field
with st.container():
    # header that is shown on the web UI
    # st.subheader('Image File Upload:')
    # the image upload field, the specific ui element that allows you to upload an image
    # when an image is uploaded it saves the file to the directory, and creates a path to that image
    File = st.file_uploader('Product image', type=["png", "jpg", "jpeg"], key="new")
    
    # product_keyword = st.text_input("keywords")
    # product_bullet = st.text_area("产品卖点")

    # this is the button that triggers the invocation of the model, processing of the image and/or question
    result = st.button("Click Create listing")

    user_prompt = 'If you were an excellent Amazon e-commerce product listing specialist.\
        please refer to best seller products on amazon and product image to create product listing \
        In your output, I only need the actual JSON array output. Do not include any other descriptive text related to human interaction. \
        output format: \
        {\
            "title": "title",\
            "bullets": "bullets",\
            "description": "description"\
        }\
        '

    # this is the text box that allows the user to insert a question about the uploaded image or a question in general
    if "product_title" not in st.session_state:
        st.session_state.product_title = ""
    product_tile = st.text_input("Product Title", st.session_state.product_title)

    if "product_bullet" not in st.session_state:
        st.session_state.product_bullet = ""
    product_bullet = st.text_area("Bullet Points", st.session_state.product_bullet)

    if "product_desc" not in st.session_state:
        st.session_state.product_desc = ""
    product_desc = st.text_area("Description", st.session_state.product_desc)

    # if the button is pressed, the model is invoked, and the results are output to the front end
    if result:
        # if an image is uploaded, a file will be present, triggering the image_to_text function
        if File is not None:
            # the image is displayed to the front end for the user to see
            st.image(File)
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
                st.success(f'Image {File.name} is successfully saved!')
                # running the image to text task, and outputting the results to the front end
                file_name = save_path

                output = image_to_text(file_name, user_prompt)
                st.write(output)

                data = json.loads(output)
                
                st.session_state.product_title = data['title']
                st.session_state.product_bullet = data['bullets']
                st.session_state.product_desc = data['description']
                
                # removing the image file that was temporarily saved to perform the question and answer task
                os.remove(save_path)

                st.rerun()
        # if an Image is not uploaded, but a question is, the text_to_text function is invoked
        else:
            # running a text to text task, and outputting the results to the front end
            st.write(text_to_text(user_prompt))