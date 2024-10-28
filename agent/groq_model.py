import requests
import json
import os 
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
load_dotenv()

class GroqJsonModel:
    def __init__(self, temperature=0.3, model="llama-3.1-70b-versatile"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.temperature = temperature
        self.model = model
        self.model_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json', 
            'Authorization': f'Bearer {self.api_key}'
        }

    def invoke(self, messages):
        # Properly format messages for the API call
        messages_call = []
        for msg in messages:
            messages_call.append({
                "role": msg["role"],
                "content": msg["content"]
            })

        payload = {
            "model": self.model,
            "messages": messages_call,
            "temperature": self.temperature,
            "response_format": {"type": "json_object"}
        }

        try:
            response = requests.post(
                self.model_endpoint, 
                headers=self.headers, 
                json=payload
            )
            response.raise_for_status()
            
            response_json = response.json()
            
            if 'choices' not in response_json or len(response_json['choices']) == 0:
                raise ValueError("No choices in response")
                
            content = response_json['choices'][0]['message']['content']
            
            # Attempt to parse the content as JSON
            try:
                parsed_content = json.loads(content)
                # Convert the response to an AIMessage
                return AIMessage(content=json.dumps(parsed_content))
            except json.JSONDecodeError:
                # If parsing fails, wrap the content in a JSON object
                wrapped_content = {"response": content}
                return AIMessage(content=json.dumps(wrapped_content))

        except requests.RequestException as e:
            error_content = {"error": f"Request error: {str(e)}"}
            return AIMessage(content=json.dumps(error_content))
        except (ValueError, KeyError) as e:
            error_content = {"error": f"Error in processing response: {str(e)}"}
            return AIMessage(content=json.dumps(error_content))

class GroqModel:
    def __init__(self, temperature=0.3, model="llama-3.1-70b-versatile"):
        self.api_key = os.getenv("GROQ_API_KEY")
        self.temperature = temperature
        self.model = model
        self.model_endpoint = "https://api.groq.com/openai/v1/chat/completions"
        self.headers = {
            'Content-Type': 'application/json', 
            'Authorization': f'Bearer {self.api_key}'
        }
    def invoke(self, messages):

            system = messages[0]["content"]
            user = messages[1]["content"]

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": f"system:{system}\n\n user:{user}"
                    }
                ],
                "temperature": self.temperature,
            }

            try:
                request_response = requests.post(
                    self.model_endpoint, 
                    headers=self.headers, 
                    data=json.dumps(payload)
                    )
                
                print("REQUEST RESPONSE", request_response)
                request_response_json = request_response.json()['choices'][0]['message']['content']
                response = str(request_response_json)
                
                response_formatted = AIMessage(content=response)

                return response_formatted
            except requests.RequestException as e:
                response = {"error": f"Error in invoking model! {str(e)}"}
                response_formatted = AIMessage(content=response)
                return response_formatted


# if __name__ == "__main__":
#     groq_model = GroqModel()
#     messages = [
#         {
#             "role": "system", 
#             "content": """
#             You are a reporter. You will be presented with a webpage containing information relevant to the research question.
# """
#         },
#         {
#             "role": "user",
#             "content": "question what is LLM ?"
#         }
#     ]
#     result = groq_model.invoke(messages)
#     print(result.content)
