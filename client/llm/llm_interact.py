from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI()
def send_llm(prompt,prev_q_id):
    response = client.responses.create(
        model="gpt-4.1-nano",
        input=prompt,
        previous_response_id=prev_q_id
    )
    return (response.output_text, response.id)
