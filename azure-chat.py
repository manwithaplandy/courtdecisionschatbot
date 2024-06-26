from typing import Callable
import gradio as gr
import os
import time
from server import process_question, process_file
from config import edit_config, get_config

# Chatbot demo with multimodal input (text, markdown, LaTeX, code blocks, image, audio, & video). Plus shows support for streaming text.

getResponse: Callable[[str], str] = process_question

lastText = ""

def set_get_response(get_response: Callable[[str], str]):
    getResponse = get_response

def add_text(history, text):
    global lastText
    lastText = text
    history = history + [(text, None)]
    return history, gr.Textbox(value="", interactive=False)


def add_file(history, file):
    history = history + [((file.name,), None)]
    return history


def bot(history):
    global lastText
    response = getResponse(lastText)
    history[-1][1] = ""
    for chunk in response:
        history[-1][1] += chunk
        yield history

# Create an instance of the edit_config function
config_interface = edit_config(get_config())

with gr.Blocks(title="AI") as markdown_bot:
    with gr.Tab(label="Chatbot"):
        gr.Interface(process_file, "files", outputs=gr.Label(label="Result of import"), title="Upload a pdf, docx or JSON file", allow_flagging="never")
        chatbot = gr.Chatbot(
            [],
            elem_id="chatbot",
            bubble_full_width=False,
            label="Chat with the AI",
            avatar_images=(None, (os.path.join(os.path.dirname(__file__), "OIP.jpg"))),
        )

        with gr.Row():
            txt = gr.Textbox(
                scale=4,
                show_label=False,
                placeholder="Enter text and press enter...",
                container=False,
            )
            #btn = gr.UploadButton("📁", file_types=["image", "video", "audio"])

        txt_msg = txt.submit(add_text, [chatbot, txt], [chatbot, txt], queue=False).then(
            bot, chatbot, chatbot, api_name="bot_response"
        )
        txt_msg.then(lambda: gr.Textbox(interactive=True), None, [txt], queue=False)
        #file_msg = btn.upload(add_file, [chatbot, btn], [chatbot], queue=False).then(
        #    bot, chatbot, chatbot
        #)
    with gr.Tab("Edit Config"):
        config_interface.render()
    #gr.Interface #.add(config_interface.clear())
    #edit_config_tab.children = [config_interface]
        
    

markdown_bot.queue()
lastText = ""

markdown_bot.launch(share=True)