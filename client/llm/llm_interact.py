from dotenv import load_dotenv

load_dotenv()

def send_llm(prompt,prev_q_id, client):
    response = client.responses.create(
        model="gpt-4.1-nano",
        instructions = "You are a statue of Enzo Ferrari in a museum. Guests will be asking you questions regarding yourself," \
                        " your life, the history of Ferrari. Guests will also be asking you general questions unrelated to yourself." \
                        "Keep the responses brief and concise, but add a little flare to make them less serious.",
        input=prompt,
        previous_response_id=prev_q_id
    )
    return (response.output_text, response.id)
