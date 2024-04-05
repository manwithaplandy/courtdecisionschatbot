# Import the required libraries
import gradio as gr
import pdfplumber
import json
import openai
import os
import logging
import dotenv
import docx
from document_analysis import JudgeDecision2116278PDF
from discord.utils import escape_markdown
from config import get_config


def set_get_response(s):
  pass
#markdown_bot = None

# Load the environment variables
dotenv.load_dotenv()
openai.api_type = os.getenv("OPENAI_API_TYPE")
openai.api_base = os.getenv("AZURE_OPENAI_BASE_URL")
openai.api_version = os.getenv("AZURE_OPENAI_API_VERSION")
openai.api_key = os.getenv("OPENAI_API_KEY")

conversation = []

document_text = ""

def process_json(json_file: str):
    docana: JudgeDecision2116278PDF = None
    with open(json_file, "r", encoding='utf-8') as raw_json:
      temp = json.load(raw_json) #, object_hook=JudgeDecision2116278PDF);
      docana = JudgeDecision2116278PDF(temp)
      fullText = ""
      for paragraph in docana.analyzeResult['paragraphs']:
        fullText = f"{fullText}\n{paragraph['content']}"
      document_text = fullText
      return fullText

# code to process the uploaded MS Word file to string
def process_word(file):
  # Check the file type and extract the text
  if(file is None):
    return "Please upload a file."
  if file.name.endswith(".docx"):
    # Use docx to read the docx file
    doc = docx.Document(file)
    text = ""
    # Loop through the paragraphs and append the text
    for para in doc.paragraphs:
      text += para.text
  else:
    # Return an error message if the file type is not supported
    return "Sorry, I can only process docx files."
  return text


# Define the function to process the uploaded file and create an OpenAI chat
def process_file(file):
  # Check the file type and extract the text
  if(file is None):
    return "Please upload a file."
  text = ""
  if file.name.endswith(".pdf"):
    # Use pdfplumber to read the pdf file
    pdf = pdfplumber.open(file)
    # Loop through the pages and append the text
    for page in pdf.pages:
      text += page.extract_text()
    pdf.close()
  elif file.name.endswith(".json"):
    # Use json to load the json file
    text = process_json(file)
  elif file.name.endswith(".docx"):
    # Use docx to read the docx file
    text = process_word(file)
  else:
    # Return an error message if the file type is not supported
    return "Sorry, I can only process docx, pdf or json files."
  if(text is None or len(text) == 0):
    return "No file was updated or the file is empty. Please upload a file with content."
  instruction_message = config.instruction_message.replace("$1", text)
  conversation.append(
                {
                   "role":"system",
                   "content": instruction_message
                }
               );
  set_get_response(process_question)
  # Launch the interface
  
  
  return "Your chat is ready. Please enter your question in the textbox below."

def process_question(question: str):
  # Use OpenAI to create a chat based on the text
  # Set the engine and the temperature
  if(question is None or len(question) == 0):
    return "Please enter a question."
  # engine = os.getenv("OPENAI_ENGINE_ID") or "davinci"
  # temperature = float(os.getenv("OPENAI_TEMPERATURE") or 0.5)
  # Create a prompt with the text and a question
  #prompt = f"The following is a court decision:\n{document_text}\n\nQ: "
  # Use gr.Interface to create a chat interface
  conversation.append({
      "role": "user",
      "content": question
    })

  completion = openai.chat.completions.create(
        model=engine,
        messages = conversation,
        temperature=temperature,
        max_tokens=4000,
        top_p=0.95,
        frequency_penalty=0,
        presence_penalty=0,
        stream=True,
        stop=None
      )
  content = ""
  role = "assistant"
  for chunk in completion:
    if len(chunk.choices)  > 0:
      try:
        if(chunk.choices[0].delta.content is None):
          continue;
        if(chunk.choices[0].finish_reason == "length" or chunk.choices[0].finish_reason == "content_filter"):
          content = content + f" (error reason: {chunk.choices[0].finish_reason})"
          print(f"stop reason: {chunk.choices[0].finish_reason}")
          yield f" (error reason: {chunk.choices[0].finish_reason})"
          break
        content = content + chunk.choices[0].delta.content
        # role = chunk.choices[0].delta.role;
        yield chunk.choices[0].delta.content
      except Exception as e:
        logging.error(e)
        print(e)
  
  conversation.append({
      "role": role,
      "content": content
    })
  yield ""
  
# Create a gradio app to upload the file and process it
app = gr.Interface(
  # Define the function to process the file
  fn = process_file,
  # Define the input and output components
  inputs = gr.File(label="Upload a court decision pdf or json file"),
  outputs = "text",
  # Define the title and the description
  title = "Court Decision Chat",
  description = "This is a gradio app that allows you to upload a court decision pdf or json file and create an OpenAI chat based on it. You can ask questions about the court decision and get answers from OpenAI."
)
# Launch the app
#app.launch()

if __name__ == "__main__":
    app.launch(show_api=True, share=True)   