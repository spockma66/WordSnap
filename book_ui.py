import tkinter as tk
import globals  
import requests
import json
import threading
import subprocess
import queue
import re
import os
from tkinter import font
from utils import load_config, load_ui_config, load_tts_config, logger

class BookUI:
    def __init__(self):
        logger.info("UI initializing started")
        
        self.__master = tk.Tk()
        self.__ui_config = load_ui_config()
        logger.info("Config loaded")
        
        # Maximizing the window
        self.__master.geometry(f"{self.__master.winfo_screenwidth()}x{self.__master.winfo_screenheight()}")
        self.__master.title("Just like reading a book")
        self.__master.protocol("WM_DELETE_WINDOW", self.__on_close)
        self.__current_spread = 0  # Index of current two-page
        self.__highlight_vocab = self.__get_hl_vocab()
        # Initial instruction of book UI
        self.__texts = [
                           "Page 1: Generating content...",
                           "Page 2: Tap or click on a word and its explanation will be shown below!",
                       ]
        self.__explaining_thread = None
        self.__STREAM_END_MARKER = None
        
        self.__setup_ui()
        
        logger.info("UI initializing ended")
         
         
    def __get_hl_vocab(self):
        logger.info("Assembling hightlight vocabulary")
        
        config = load_config()
        file_list = config.get('highlight_vocab_list')
        logger.info("Config loaded")
        
        vocab = set()
        for file_path in file_list:
            logger.debug("Adding %s to the highlight vocabulary", file_path)
            if os.path.isfile(file_path):
                with open(file_path, 'r', encoding='utf-8') as file:
                    vocab.update({line.strip() for line in file}) 
        
        if len(vocab) == 0:
            logger.warning("Highlight vocabulary currently unavailable")
            
        return vocab
    
    
    def __setup_ui(self):
        logger.info("UI setup started")
        
        self.__page_frame = tk.Frame(self.__master)
        self.__page_frame.grid(row=0, column=0, sticky="nsew")

        # Setting weights of master window and making sure it fills the whole space
        self.__master.grid_rowconfigure(0, weight=1)
        self.__master.grid_columnconfigure(0, weight=1)

        # Setting weights on page_frame
        self.__page_frame.grid_columnconfigure(1, weight=1)
        self.__page_frame.grid_columnconfigure(2, weight=1)
        self.__page_frame.grid_rowconfigure(0, weight=2)  # Page area
        self.__page_frame.grid_rowconfigure(1, weight=0)  # Separating lines
        self.__page_frame.grid_rowconfigure(2, weight=3)  # Explanation area
        self.__page_frame.grid_rowconfigure(3, weight=0)  # Pause button

        # Previous page button on the left
        self.__left_button = tk.Button(self.__page_frame, text="<", command=self.__show_previous_page)
        self.__left_button.grid(row=0, column=0, rowspan=3, padx=10, pady=10, sticky="ns")  

        # Left page related
        self.__left_page_frame = tk.Frame(self.__page_frame)
        self.__left_page_frame.grid(row=0, column=1, padx=20, pady=10, sticky="nsew")
        self.__left_page_frame.grid_rowconfigure(0, weight=1)
        self.__left_page_frame.grid_columnconfigure(0, weight=1)

        self.__left_page = tk.Text(
            self.__left_page_frame,
            wrap="word",
            font=(self.__ui_config['normal_text']['font_family'], self.__ui_config['normal_text']['font_size']),
            bg=self.__ui_config['text_bg_color'],
            relief="sunken"
        )
        self.__left_page.grid(row=0, column=0, sticky="nsew")

        self.__left_page_scrollbar = tk.Scrollbar(
            self.__left_page_frame,
            orient="vertical",
            width=20,
            command=lambda *args: self.__on_scroll(self.__left_page, *args)
        )
        self.__left_page_scrollbar.grid(row=0, column=1, sticky="ns")
        self.__left_page.config(yscrollcommand=self.__left_page_scrollbar.set)

        # Right page related
        self.__right_page_frame = tk.Frame(self.__page_frame)
        self.__right_page_frame.grid(row=0, column=2, padx=20, pady=10, sticky="nsew")
        self.__right_page_frame.grid_rowconfigure(0, weight=1)
        self.__right_page_frame.grid_columnconfigure(0, weight=1)

        self.__right_page = tk.Text(
            self.__right_page_frame,
            wrap="word",
            font=(self.__ui_config['normal_text']['font_family'], self.__ui_config['normal_text']['font_size']),
            bg=self.__ui_config['text_bg_color'],
            relief="sunken"
        )
        self.__right_page.grid(row=0, column=0, sticky="nsew")

        self.__right_page_scrollbar = tk.Scrollbar(
            self.__right_page_frame,
            orient="vertical",
            width=20,
            command=lambda *args: self.__on_scroll(self.__right_page, *args)
        )
        self.__right_page_scrollbar.grid(row=0, column=1, sticky="ns")
        self.__right_page.config(yscrollcommand=self.__right_page_scrollbar.set)

        # Next page button on the right
        self.__right_button = tk.Button(self.__page_frame, text=">", command=self.__show_next_page)
        self.__right_button.grid(row=0, column=3, rowspan=3, padx=10, pady=10, sticky="ns")  

        # Separating lines between page content and explanation content
        self.__left_separator = tk.Frame(self.__page_frame, height=2, bd=1, relief="sunken")
        self.__left_separator.grid(row=1, column=1, padx=20, pady=5, sticky="ew")
        self.__right_separator = tk.Frame(self.__page_frame, height=2, bd=1, relief="sunken")
        self.__right_separator.grid(row=1, column=2, padx=20, pady=5, sticky="ew")
        
        # Left explanation related
        self.__left_explanation_frame = tk.Frame(self.__page_frame)
        self.__left_explanation_frame.grid(row=2, column=1, padx=20, pady=10, sticky="nsew")
        self.__left_explanation_frame.grid_rowconfigure(0, weight=1)
        self.__left_explanation_frame.grid_columnconfigure(0, weight=1)

        self.__explanation_text_left = tk.Text(
            self.__left_explanation_frame,
            wrap="word",
            font=(self.__ui_config['explanation_text']['font_family'], self.__ui_config['explanation_text']['font_size']),
            fg=self.__ui_config['explanation_text']['font_color'],
            bg=self.__ui_config['text_bg_color'],
        )
        self.__explanation_text_left.grid(row=0, column=0, sticky="nsew")

        self.__left_explanation_scrollbar = tk.Scrollbar(
            self.__left_explanation_frame,
            orient="vertical",
            width=20,
            command=lambda *args: self.__on_scroll(self.__explanation_text_left, *args)
        )
        self.__left_explanation_scrollbar.grid(row=0, column=1, sticky="ns")
        self.__explanation_text_left.config(yscrollcommand=self.__left_explanation_scrollbar.set)

        # right explanation related
        self.__right_explanation_frame = tk.Frame(self.__page_frame)
        self.__right_explanation_frame.grid(row=2, column=2, padx=20, pady=10, sticky="nsew")
        self.__right_explanation_frame.grid_rowconfigure(0, weight=1)
        self.__right_explanation_frame.grid_columnconfigure(0, weight=1)

        self.__explanation_text_right = tk.Text(
            self.__right_explanation_frame,
            wrap="word",
            font=(self.__ui_config['explanation_text']['font_family'], self.__ui_config['explanation_text']['font_size']),
            fg=self.__ui_config['explanation_text']['font_color'],
            bg=self.__ui_config['text_bg_color'],
        )
        self.__explanation_text_right.grid(row=0, column=0, sticky="nsew")

        self.__right_explanation_scrollbar = tk.Scrollbar(
            self.__right_explanation_frame,
            orient="vertical",
            width=20,
            command=lambda *args: self.__on_scroll(self.__explanation_text_right, *args)
        )
        self.__right_explanation_scrollbar.grid(row=0, column=1, sticky="ns")
        self.__explanation_text_right.config(yscrollcommand=self.__right_explanation_scrollbar.set)

        # Button to control image capture at the bottom
        self.__pause_button = tk.Button(
            self.__page_frame,
            height=2,
            text="Pause Image Capture",
            font=(self.__ui_config['button_text']['font_family'], self.__ui_config['button_text']['font_size']),
            command=self.__toggle_pause          
        )
        self.__pause_button.grid(row=3, column=1, columnspan=2, padx=20, sticky="ew")
        
        # Make sure the page is self-adaptive
#         self.__page_frame.grid_columnconfigure(1, weight=1)
#         self.__page_frame.grid_columnconfigure(2, weight=1)

        # Show content of current spread
        self.show_spread(self.__texts)
        
        logger.info("UI setup ended")
    
    
    def __on_scroll(self, widget, *args):
        # Any operation on the page would pause image capture
        globals.CAPTURE_PAUSED = True
        self.__pause_button.config(text="Resume Image Capture")
        logger.debug("CAPTURE_PAUSED is set to True in __on_scroll")
        
        widget.yview(*args)
        
    
    def __split_text(self, text):
        # Fully split the text by 2 steps to fix unrecognized spaces from ocr result
        logger.info("Text split started")
        
        space_sep_text = text.split()
        words = []
        pattern = r'[^a-zA-Z\']+'
        for snippet in space_sep_text:
            match_ends = [match.end() for match in re.finditer(pattern, snippet)]
            if match_ends is None or len(match_ends) == 0:
                words.append(snippet)
            else:
                last_end = 0
                for i, match_end in enumerate(match_ends):
                    if match_end == 1:
                        if i < (len(match_ends) - 1):
                            continue
                        words.append(snippet[last_end:])
                    else:
                        words.append(snippet[last_end:match_end])
                        last_end = match_end
                        if i == (len(match_ends) - 1) and match_end < len(snippet) :
                            words.append(snippet[last_end:])       
        
        logger.info("Text split ended")
        return words
        
        
    def __populate_page(self, page_widget, text, side):
        logger.info("Page populating started")
        
        # Fully split text into words
        words = self.__split_text(text)
        
        # Show each word on the page and make it responsive to touch
        word_cnt = 0
        for index, raw_word in enumerate(words):
            split_raw_word = re.split(r"[^a-zA-Z\'0-9-]+", raw_word)
            word = None
            
            # Find the real word after removing English symbols from raw word
            for w in split_raw_word:
                if w != '':
                    word = w
                    break
            
            if word is None:
                continue
            else:
                word_cnt += 1
        
            highlight_word_tag = "highlight_" + str(index)
            normal_word_tag = "normal_" + str(index)
            # Deciding which style to use for current word and setting click event
            if self.__highlight_vocab is None or len(self.__highlight_vocab) == 0 or word not in self.__highlight_vocab:
                page_widget.insert(tk.END, raw_word + " ", normal_word_tag)
                page_widget.tag_config(normal_word_tag, font=(self.__ui_config['normal_text']['font_family'], self.__ui_config['normal_text']['font_size']), foreground=self.__ui_config['normal_text']['font_color'])
                page_widget.tag_bind(normal_word_tag, "<Button-1>", lambda e, w=word: self.__show_word_explanation(w, text, side))
            else:
                page_widget.insert(tk.END, raw_word + " ", highlight_word_tag)
                page_widget.tag_config(highlight_word_tag, font=(self.__ui_config['highlight_text']['font_family'], self.__ui_config['highlight_text']['font_size']), foreground=self.__ui_config['highlight_text']['font_color'])
                page_widget.tag_bind(highlight_word_tag, "<Button-1>", lambda e, w=word: self.__show_word_explanation(w, text, side))
            
            # Making a line breaking when necessary
            if word_cnt > int(self.__ui_config.get('line_breaking_threshold')) and raw_word[-1] in [".", "?", "!"]:
                page_widget.insert(tk.END, "\n\n", "line_breaking")
                word_cnt = 0
        
        logger.info("Page populating ended")
    
    
    def __pronounce_the_word(self, word):
        # Any operation on the page would pause image capture
        globals.CAPTURE_PAUSED = True
        self.__pause_button.config(text="Resume Image Capture")
        logger.debug("CAPTURE_PAUSED is set to True in __pronounce_the_word")
        
        if globals.EXPLAINING == True:
            logger.info("Pronouncing currently unavailable due to word explaining")
            return
        
        os.system("aplay sound/beep.wav")
        logger.info("Pronouncing started")
        
        config = load_tts_config()
        logger.info("Config loaded")
        
        command = [
            str(config.get("sherpa_model_path")),
            f"--num-threads={str(config.get('num_threads'))}",
            f"--vits-model={str(config.get('vits_model'))}",
            f"--vits-tokens={str(config.get('vits_tokens'))}",
            f"--vits-data-dir={str(config.get('vits_data_dir'))}",
            f"--vits-length-scale={str(config.get('vits_length_scale'))}",
            f"--output-filename=sound/last_pronunciation.wav",
            f"This word is pronounced as - {word}."
            ]
        
        logger.debug("Command ready: %s", command)
        process = subprocess.run(command, capture_output=True, text=True)
        logger.info("Command executed")
        
        if process.returncode != 0:
            logger.error("Error occurred when pronouncing: %s", process.stderr)
        
        logger.info("Pronouncing ended")
        
        
    def __update_text_widget(self, text_widget, input_queue, side, pronunciation_hint, word):        
        try:
            while True:
                text = input_queue.get_nowait()
                if text is self.__STREAM_END_MARKER:
                    input_queue.queue.clear()
                    
                    if side == "left":
                        text_widget.insert(tk.END, "\n\n" + pronunciation_hint + word + "\n", "left_word")
                        text_widget.tag_bind("left_word", "<Button-1>", lambda e, w=word: self.__pronounce_the_word(w))
                    elif side == "right":
                        text_widget.insert(tk.END, "\n\n" + pronunciation_hint + word + "\n", "right_word")
                        text_widget.tag_bind("right_word", "<Button-1>", lambda e, w=word: self.__pronounce_the_word(w))
                    text_widget.see(tk.END)
                    
                    globals.EXPLAINING = False
                    logger.info("Updating %s explanation widget is done and EXPLAINING is set to False", side)
                    return
                text_widget.insert(tk.END, text)
                text_widget.see(tk.END)
        except queue.Empty:
            pass

        text_widget.after(100, lambda: self.__update_text_widget(text_widget, input_queue, side, pronunciation_hint, word))

    
    def __get_word_explanation(self, word, full_text, side, output_queue):        
        logger.info("Getting word explanation started")
        
        config = load_config()
        url = config.get("ollama_api")["url"]
        data = config.get("ollama_api")["data"]
        data["prompt"] = data["prompt"].format(word=word, full_text=full_text)
        logger.debug("Sending ollama request with data: %s", data)
 
        try:
            with requests.post(url, json=data, stream=True) as response:

                if response.status_code != 200:
                    logger.error("Error occurred when getting response, status code: %s", response.status_code)
                    logger.error("Response text is: %s", response.text)
                    
                    output_queue.put(STREAM_END_MARKER)  
                    return
                
                if side == "left":
                    self.__explanation_text_left.delete(1.0, tk.END)
                elif side == "right":
                    self.__explanation_text_right.delete(1.0, tk.END)

                for line in response.iter_lines():
                    if line:
                        try:
                            json_data = json.loads(line.decode('utf-8'))
                            delta_text = json_data.get('response', '')
                            output_queue.put(delta_text)
                        except json.JSONDecodeError:
                            logger.error("Received invalid json data")

            output_queue.put(self.__STREAM_END_MARKER)
            logger.info("Received the whole response")
        except requests.exceptions.RequestException as e:
            output_queue.put(self.__STREAM_END_MARKER) 
            logger.error("Ollama request exception: %s", e)
    
    
    def __show_word_explanation(self, word, full_text, side):
        # Any operation on the page would pause image capture
        globals.CAPTURE_PAUSED = True
        self.__pause_button.config(text="Resume Image Capture")
        logger.debug("CAPTURE_PAUSED is set to True in __show_word_explanation")
        
        if globals.EXPLAINING:
            logger.warning('Explaining currently unavailable because the previous task is still unfinished')
            return
        else:
            globals.EXPLAINING = True
        
        logger.info("Showing word explanation started and EXPLAINING is set to True")
        
        config = load_config()
        pronunciation_hint = config.get("pronunciation_hint")
        token_queue = queue.Queue()
        
        if side == "left":
            self.__explanation_text_left.delete(1.0, tk.END)
            self.__explanation_text_left.insert(tk.END, "Generating explanation...", "left_status")
            
            self.__explaining_thread = threading.Thread(target=self.__get_word_explanation, args=(word, full_text, side, token_queue), daemon=True)
            self.__explaining_thread.start()
            self.__update_text_widget(self.__explanation_text_left, token_queue, "left", pronunciation_hint, word)
        elif side == "right":
            self.__explanation_text_right.delete(1.0, tk.END)
            self.__explanation_text_right.insert(tk.END, "Generating explanation...", "right_status")
            
            self.__explaining_thread = threading.Thread(target=self.__get_word_explanation, args=(word, full_text, side, token_queue), daemon=True)
            self.__explaining_thread.start()
            self.__update_text_widget(self.__explanation_text_right, token_queue, "right", pronunciation_hint, word)
        
        logger.info("Showing word explanation ended")


    def __show_previous_page(self):
        # Any operation on the page would pause image capture
        globals.CAPTURE_PAUSED = True
        self.__pause_button.config(text="Resume Image Capture")
        logger.debug("CAPTURE_PAUSED is set to True in __show_previous_page")
        
        if globals.EXPLAINING:
            return
        
        if self.__current_spread > 0:
            self.__current_spread -= 1
            self.show_spread()


    def __show_next_page(self):
        # Any operation on the page would pause image capture
        globals.CAPTURE_PAUSED = True
        self.__pause_button.config(text="Resume Image Capture")
        logger.debug("CAPTURE_PAUSED is set to True in __show_next_page")
        
        if globals.EXPLAINING:
            return
        
        if self.__current_spread < ((len(self.__texts) + 1) // 2) - 1:
            self.__current_spread += 1
            self.show_spread()


    def __toggle_pause(self):
        if globals.CAPTURE_PAUSED:
            globals.CAPTURE_PAUSED = False
            self.__pause_button.config(text="Pause Image Capture")
            logger.debug("CAPTURE_PAUSED is set to False in __toggle_pause")
        else:
            globals.CAPTURE_PAUSED = True
            self.__pause_button.config(text="Resume Image Capture")
            logger.debug("CAPTURE_PAUSED is set to True in __toggle_pause")
    
    
    def __on_close(self):
        globals.CLOSING = True
        if self.__explaining_thread is not None:
            self.__explaining_thread.join()
        self.__master.destroy()
    
    
    def start_working(self):
        self.__master.mainloop()
        logger.info("UI main loop started")
            
            
    def show_spread(self, texts=None):
        # Initializing for new list of text content 
        if texts is not None:
            self.__texts = texts
            self.__current_spread = 0
            
        # Clear previous content on pages
        self.__left_page.delete(1.0, tk.END)
        self.__right_page.delete(1.0, tk.END)
        self.__explanation_text_left.delete(1.0, tk.END)
        self.__explanation_text_right.delete(1.0, tk.END)

        # Show current content of both pages(a spread)
        if self.__current_spread * 2 < len(self.__texts):
            left_text = self.__texts[self.__current_spread * 2]
            self.__populate_page(self.__left_page, left_text, "left")
            
        if self.__current_spread * 2 + 1 < len(self.__texts):
            right_text = self.__texts[self.__current_spread * 2 + 1]
            self.__populate_page(self.__right_page, right_text, "right")
            
            