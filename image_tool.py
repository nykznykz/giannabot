import base64
from openai import OpenAI
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Type
from dotenv import load_dotenv

load_dotenv()


class StickerReactionInput(BaseModel):
    image_path: str = Field(description="The path to the image to describe")

class StickerReactionTool(BaseTool):
    name: str = "sticker_reaction"
    description: str = "After receiving a sticker, use this tool to formulate a reaction to it."
    args_schema: Type[BaseModel] = StickerReactionInput

    def _run(self, image_path: str) -> str:
        return get_photo_description(image_path)

# Function to encode the image
def encode_image(image_path):
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_photo_description(image_path):
    client = OpenAI()
    base64_image = encode_image(image_path)
    response = client.responses.create(
        model="gpt-4o-mini",
        input=[
        {
            "role": "user",
            "content": [
                { "type": "input_text", "text": "Reply in this format: <IMAGE DESCRIPTION>: Some description of the image. <WITTY RESPONSE>: A one sentence witty and humorous in reponse to the image. Include emojis to keep this lighthearted and fun." },
                {
                    "type": "input_image",
                    "image_url": f"data:image/jpeg;base64,{base64_image}",
                },
            ],
        }
    ],
    )
    return response.output_text
