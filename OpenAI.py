import json
import time
from Config import Config
from openai import AzureOpenAI
import openai
import logging

class OpenAI:
    def __init__(self):
        config=Config()
        self.key=config.AZURE_OPENAI_KEY
        self.base=config.AZURE_OPENAI_BASE
        self.version=config.AZURE_OPENAI_VERSION
        self.client=AzureOpenAI(azure_endpoint = self.base,api_version =self.version,api_key=self.key)
        self.model=config.AZURE_OPENAI_MODEL

    
    def call_gpt_endpoint(self,prompt:str)->dict:         
        for i in range(5): # Try up to 10 times  
            try:
                response = self.client.chat.completions.create(
                        model=self.model,
                        messages = [
                            {"role":"system","content":"You are an AI assistant that helps people find information."},   
                            {"role":"user","content":f"{prompt}"}
                        ],  
                        temperature=0,  
                        max_tokens=4096,  
                        top_p=0.95,  
                        frequency_penalty=0,  
                        presence_penalty=0,  
                        stop=None)   
                try:
                        response_json=json.loads(response.choices[0].message.content)     
                        return response_json
                except Exception as e:
                        logging.error("Error in response: "+str(e))
            except (openai.RateLimitError,openai.APIStatusError,openai.BadRequestError,openai.APIConnectionError) as e:  
                if i == 4:
                        # If we've already tried 10 times, give up and return an error message
                        logging.error("Failed after 5 attempts")                          
                        return {}
                else:  
                        logging.info("Retrying")
                        time.sleep(i*30) # Wait 1 minute before retrying