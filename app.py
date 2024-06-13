import base64
import string
import streamlit as st
from pathlib import Path
import os
import json
from dotenv import load_dotenv
from listing_voc_prompt import image_to_text, text_to_text, gen_listing_prompt, gen_voc_prompt
from listing_voc_agents import create_listing


# load environment variables
load_dotenv()

st.sidebar.header("AI Listing/VOC")
st.sidebar.write("AI Listing/VOC with Amazon Bedrock and Claude 3")

option = st.sidebar.selectbox(
    'Function Choicer',
    ('AI Listing', 'VOC'))

# country_options = ['USA', 'Singapore']
# country_options_key = {"USA":"com", "Singapore":"sg"}
# country_lable = st.sidebar.selectbox('Select Country', country_options)

# title of the streamlit app
# st.title(f""":rainbow[{option} with Amazon Bedrock and Claude 3]""")

if option == 'AI Listing':
    
    mode_options = ['Agent', 'PE']
    mode_lable = st.sidebar.selectbox('Select Mode', mode_options)

    # default listing container that houses the image upload field
    with st.container():
        # header that is shown on the web UI
        # st.subheader('Image File Upload:')
        # the image upload field, the specific ui element that allows you to upload an image
        # when an image is uploaded it saves the file to the directory, and creates a path to that image
        File = st.file_uploader('Product image', type=["png", "jpg", "jpeg"], key="new")
        brand = st.text_input("Brand", 'Stanley')
        features = st.text_input("Product Short Description")

        asin = st.text_input("Reference Amazon ASIN", 'B0BZYCJK89')

        # this is the button that triggers the invocation of the model, processing of the image and/or question
        result = st.button("Submit")

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

                    if mode_lable == 'PE':
                        user_prompt = gen_listing_prompt(asin, 'com', brand, features)
                        print(user_prompt)
                        
                        output = image_to_text(file_name, user_prompt)
                        #st.write(output)
                    elif mode_lable == 'Agent':
                        response = create_listing(asin, file_name, brand, features)
                        rslist = str(response['output']).rsplit('>')
                        output = rslist[-1]

                    data = json.loads(output)

                    st.write("Title:\n")
                    st.write(data['title'])

                    # #get all string from bullet points data['bullets']
                    st.write("Bullet Points:\n")
                    bullet_points = ""
                    for item in data['bullets']:
                        bullet_points += "• " + item + "\n\n"
                    st.markdown(bullet_points)

                    st.write("Description:\n")
                    st.write(data['description'])
                    
                    # removing the image file that was temporarily saved to perform the question and answer task
                    os.remove(save_path)

                    #st.rerun()
            # if an Image is not uploaded, but a question is, the text_to_text function is invoked
            else:
                # running a text to text task, and outputting the results to the front end
                st.write('select product image')
elif option == 'VOC':
    with st.container():
        asin = st.text_input("Amazon ASIN", 'B0BZYCJK89')

        result = st.button("Submit")

        if result:
            domain = "com"
            user_prompt = gen_voc_prompt(asin, domain)

            output = text_to_text(user_prompt)

            st.write(output)