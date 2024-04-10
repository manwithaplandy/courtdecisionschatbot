from typing import Callable
import gradio as gr
import os
import time
from server import process_question, process_file, save_file, conversation, logger
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
    response_generator = getResponse(lastText)  # This is a generator now
    history[-1][1] = ""
    try:
        for chunk in response_generator:
            history[-1][1] += chunk
            yield history
    except StopIteration as e:
        save_file_path = e.value  # This is the return value of process_question
        return save_file_path

last_size = 0

def download_file():
    global conversation
    if (last_size != len(conversation) and conversation and conversation[-1]):
        save_file_path = save_file(conversation)
        file_name, file_path = save_file_path
    return file_path

# Create an instance of the edit_config function
config_interface = edit_config(get_config())

with gr.Blocks(title="AI") as markdown_bot:
    with gr.Tab(label="Chatbot"):
        gr.Interface(
            process_file, 
            "files", 
            outputs=gr.Label(label="Result of import"), 
            title="Upload a pdf, docx or JSON file", 
            allow_flagging="never"
        )
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
        
        with gr.Row("Process and download"):
            gr_outputs = [
                gr.File(
                    label="Output File",
                    file_count="single",
                    file_types=[".txt", ".text"]
                    )
                ]
            gr_submit_button = gr.Button("Save last response to file")

        gr_submit_button.click(download_file, None, gr_outputs)

        txt_msg = txt.submit(
            fn=add_text, 
            inputs=[chatbot, txt], 
            outputs=[chatbot, txt], 
            queue=False).then(
            fn=bot, 
            inputs=chatbot, 
            outputs=chatbot, 
            api_name="bot_response"
        )
        txt_msg.then(
            fn=lambda: gr.Textbox(interactive=True), 
            inputs=None, 
            outputs=[txt], 
            queue=False
        )
        # logger.info("msg complete - download file time")
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