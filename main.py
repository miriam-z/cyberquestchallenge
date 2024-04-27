import anthropic
from dotenv import load_dotenv
import os

load_dotenv()

client = anthropic.Anthropic(
    api_key=os.getenv("ANTHROPIC_API_KEY")
)
message = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1000,
    temperature=0,
    system="You are an expert research assistant. Here is a document you will answer questions about:\n<doc>\n[Full text of Citibank SEC filing 10-K 2023, not pasted here for brevity]\n</doc>\n\nFirst, find the quotes from the document that are most relevant to answering the question, and then print them in numbered order. Quotes should be relatively short.\n\nIf there are no relevant quotes, write \"No relevant quotes\" instead.\n\nThen, answer the question, starting with \"Answer:\". Do not include or reference quoted content verbatim in the answer. Don't say \"According to Quote [1]\" when answering. Instead make references to quotes relevant to each section of the answer solely by adding their bracketed numbers at the end of relevant sentences.\n\nThus, the format of your overall response should look like what's shown between the <example></example> tags. Make sure to follow the formatting and spacing exactly.\n<example>\nQuotes:\n[1] \"Company X reported revenue of $12 million in 2021.\"\n[2] \"Almost 90% of revenue came from widget sales, with gadget sales making up the remaining 10%.\"\n\nAnswer:\nCompany X earned $12 million. [1] Almost 90% of it was from widget sales. [2]\n</example>\n\nIf the question cannot be answered by the document, say so.",
    messages=[
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": " Is Citibank doing well?"
                }
            ]
        }
    ]
)
print(message.content)