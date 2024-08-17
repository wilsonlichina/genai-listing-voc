import time
import boto3
import json
import base64
from PIL import Image
import io


bedrock_client = boto3.client(service_name = 'bedrock-runtime',region_name = 'us-west-2')

images='./2.webp'

def image_base64_encoder(image_path, max_size=1568):
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    img = Image.open(io.BytesIO(image_bytes))
    width, height = img.size
    img_format = img.format.lower()

    if width > max_size or height > max_size:
        if width > height:
            new_width = max_size
            new_height = int(height * (max_size / width))
        else:
            new_height = max_size
            new_width = int(width * (max_size / height))

        img = img.resize((new_width, new_height), Image.ANTIALIAS)

    resized_bytes = io.BytesIO()
    img.save(resized_bytes, format=img_format)
    resized_bytes = resized_bytes.getvalue()

    return resized_bytes, img_format


def content_moderation_image(image_filename, language_lable):

    imagedata, image_type =image_base64_encoder(image_filename)

    system_text='''
    任务: 检测用户上传的图片是否对现有市场上的品牌形象造成侵权。

    输入:
    用户上传的图片

    输出:
    {
     "infringement": <布尔值,表示是否侵权>,
      "confidence": <0到1之间的浮点数,表示置信度>,
      "reason": "<判断侵权或不侵权的原因>"
    }

    例子输出:
    {
    "infringement": true,
    "confidence": 0.9,
    "reason": "上传的图片中包含了现有品牌的注册商标,未经授权使用可能构成侵权。"
    }

    限制条件:
    - 输出中的"infringement"字段必须是布尔值
    - 输出中的"confidence"字段必须是0到1之间的浮点数
    - 输出中的"reason"字段必须是一个字符串,解释判断的原因
    - 判断侵权与否时,请考虑商标、版权等知识产权因素

    请根据上述要求,检测输入图片是否对现有品牌形象造成侵权,并生成相应的JSON输出。
'''
    system_prompts = [{"text" : system_text}]
    text='判断用户上传的图片是否侵权，使用JSON格式返回，不要做任何多余解释。'

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text":text,
                },
                {    "image": {
                        "format": image_type,
                        "source": {
                            "bytes": imagedata
                        }
                    }
                }
            ]
        }
    ]
    #Base inference parameters to use.
    inference_config = {"temperature": 0.1}
    # Additional inference parameters to use.
    additional_model_fields = {"top_k": 200}
    response = bedrock_client.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields,
    )

    return(response['output'])

#content_result=content_moderation_image(image_data,image_type)
#print(content_result)


def content_moderation_text(text):
    system_text='''
Your task is to Identify and classify any inappropriate content in user given text, Identify inappropriate content in the provided categories in the <Categories>.

</Categories>
hate,
hate/threatening,
self-harm,
sexual,
sexual/minors,
violence,
violence/graphic
</Categories>

<description>
hate: Content that expresses, incites, or promotes hate based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste. Hateful content aimed at non-protected groups (e.g., chess players) is harassment.
hate/threatening: Hateful content that also includes violence or serious harm towards the targeted group based on race, gender, ethnicity, religion, nationality, sexual orientation, disability status, or caste.
harassment: Content that expresses, incites, or promotes harassing language towards any target.
harassment/threatening:	Harassment content that also includes violence or serious harm towards any target.
self-harm: Content that promotes, encourages, or depicts acts of self-harm, such as suicide, cutting, and eating disorders.
self-harm/intent: Content where the speaker expresses that they are engaging or intend to engage in acts of self-harm, such as suicide, cutting, and eating disorders.
self-harm/instructions: Content that encourages performing acts of self-harm, such as suicide, cutting, and eating disorders, or that gives instructions or advice on how to commit such acts.
</description>

<ResponseFormat>
{
	"Moderation": false,
	"Category": "hate"
	"confidence_score": 1.0,
	"Reason":"the user content is harmful."
}
</ResponseFormat>
you should respond json only, no any other explanation.
'''
    system_prompts = [{"text" : system_text}]

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "text":text,
                }
            ]
        }
    ]
    #Base inference parameters to use.
    inference_config = {"temperature": 0.1}
    # Additional inference parameters to use.
    additional_model_fields = {"top_k": 200}
    response = bedrock_client.converse(
        modelId='anthropic.claude-3-sonnet-20240229-v1:0',
        messages=messages,
        system=system_prompts,
        inferenceConfig=inference_config,
        additionalModelRequestFields=additional_model_fields,
    )

    return(response['output'])

text='I hate everyone.'


#content_result=content_moderation_text(text)
#print(content_result)