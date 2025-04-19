from typing import Optional
from langchain.tools import BaseTool
from langchain_core.pydantic_v1 import BaseModel, Field
import requests
import os
from dotenv import load_dotenv

load_dotenv()

class SoundToolInput(BaseModel):
    text: str = Field(description="The text to convert to speech")
    voice_id: Optional[str] = Field(
        default="21m00Tcm4TlvDq8ikWAM",  # Default voice "Rachel"
        description="The ElevenLabs voice ID to use."
    )

class SoundTool(BaseTool):
    name: str = "text_to_speech"
    description: str = "Convert text to speech using ElevenLabs API and send it to Telegram. Use this tool when you want to speak to the user verbally."
    args_schema: BaseModel = SoundToolInput

    def _run(self, text: str, voice_id: Optional[str] = None) -> str:
        """Convert text to speech and send to Telegram."""
        ELEVEN_LABS_API_KEY = os.getenv("ELEVEN_LABS_API_KEY")
        if not ELEVEN_LABS_API_KEY:
            raise ValueError("ELEVEN_LABS_API_KEY not found in environment variables")

        # Set default voice if not provided
        voice_id = voice_id or "qJT4OuZyfpn7QbUnrLln"

        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": ELEVEN_LABS_API_KEY
        }

        # Generate speech using ElevenLabs API
        response = requests.post(
            f"https://api.elevenlabs.io/v1/text-to-speech/{voice_id}",
            headers=headers,
            json={
                "text": text,
                "model_id": "eleven_monolingual_v1"
            }
        )

        if response.status_code != 200:
            raise Exception(f"Failed to generate speech: {response.text}")

        # Save to temporary file
        speech_file = "data/output.mp3"
        with open(speech_file, "wb") as f:
            f.write(response.content)

        # Send to Telegram
        TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
        CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
        
        if not TOKEN or not CHAT_ID:
            raise ValueError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not found in environment variables")

        with open(speech_file, 'rb') as audio_file:
            telegram_response = requests.post(
                f'https://api.telegram.org/bot{TOKEN}/sendVoice',
                data={'chat_id': CHAT_ID},
                files={'voice': audio_file}
            )

        if telegram_response.status_code != 200:
            raise Exception(f"Failed to send to Telegram: {telegram_response.text}")

        return "Successfully generated and sent speech to Telegram"

    async def _arun(self, text: str, voice_id: Optional[str] = None) -> str:
        """Async version of the tool."""
        return self._run(text, voice_id) 