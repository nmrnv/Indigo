from pathlib import Path

import boto3
from boto3.exceptions import Boto3Error

from indigo.config import Config
from indigo.models.base import Error


class AWSClientError(Error): ...


class AWSClient:
    def __init__(self):
        config = Config.aws_config
        boto3.setup_default_session(
            aws_access_key_id=config.access_key_id,
            aws_secret_access_key=config.access_key_secret,
            region_name=config.region,
        )
        self.bucket = boto3.resource("s3").Bucket(config.bucket)
        self.polly = boto3.client("polly")

    def upload_file(self, filepath: Path):
        try:
            self.bucket.upload_file(filepath.as_posix(), filepath.name)
        except Boto3Error as e:
            raise AWSClientError(
                f"AWSClient: Upload failed with error: {e}"
            )

    def download_file(self, filename: str, filepath: Path):
        try:
            self.bucket.download_file(filename, filepath.as_posix())
        except Boto3Error as e:
            raise AWSClientError(
                f"AWSClient: Upload failed with error: {e}"
            )

    def exists(self, filename: str) -> bool:
        return any(self.bucket.objects.filter(Prefix=filename))

    def text_to_audio(self, text: str):
        try:
            # SSML: Can be used to modify the outcome
            response = self.polly.synthesize_speech(
                VoiceId="Joanna",
                OutputFormat="mp3",
                TextType="ssml",
                Text=f"<speak>{text}</speak>",
                Engine="neural",
            )

            # client = AWSClient()
            # response = client.text_to_audio("Hello. Is this unbelievable? Yes, this is unbelievable.")
            # file = open('speech.mp3', 'wb')
            # file.write(response['AudioStream'].read())
            # file.close()

            return response
        except Boto3Error:
            ...
