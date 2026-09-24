import tkinter as tk
from tkinter import ttk, scrolledtext, messagebox
from PIL import Image, ImageTk
import speech_recognition as sr
from googletrans import Translator, LANGUAGES
from gtts import gTTS
import os
import threading
import time
import pygame
import nltk
from newspaper import Article
from bs4 import BeautifulSoup as soup
from urllib.request import urlopen
import requests
from io import BytesIO

# Download the punkt tokenizer for nltk
nltk.download('punkt')

class VoiceTranslatorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Voice Translator")
        self.root.geometry("800x600")

        self.recognizer = sr.Recognizer()
        self.translator = Translator()
        self.setup_gui()
        self.language_options = list(LANGUAGES.values())

    def setup_gui(self):
        # Language selection
        self.input_lang_label = tk.Label(self.root, text="Select Input Language")
        self.input_lang_label.pack(pady=5)
        self.input_lang = ttk.Combobox(self.root, values=list(LANGUAGES.values()))
        self.input_lang.set("English")
        self.input_lang.pack(pady=5)

        self.output_lang_label = tk.Label(self.root, text="Select Output Language")
        self.output_lang_label.pack(pady=5)
        self.output_lang = ttk.Combobox(self.root, values=list(LANGUAGES.values()))
        self.output_lang.set("Spanish")
        self.output_lang.pack(pady=5)

        # Text boxes for input and output
        self.input_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=40, height=10)
        self.input_text.pack(pady=10)

        self.output_text = scrolledtext.ScrolledText(self.root, wrap=tk.WORD, width=40, height=10)
        self.output_text.pack(pady=10)

        # Buttons for actions
        self.speak_button = tk.Button(self.root, text="Speak", command=self.speak_input)
        self.speak_button.pack(pady=5)

        self.recognize_button = tk.Button(self.root, text="Recognize", command=self.recognize_speech)
        self.recognize_button.pack(pady=5)

    def speak_input(self):
        input_text = self.input_text.get("1.0", tk.END).strip()
        if input_text:
            self.translate_and_speak(input_text)

    def recognize_speech(self):
        threading.Thread(target=self._recognize_speech_thread).start()

    def _recognize_speech_thread(self):
        with sr.Microphone() as source:
            print("Listening...")
            audio = self.recognizer.listen(source)
            try:
                print("Recognizing...")
                input_lang_code = self.get_language_code(self.input_lang.get())
                input_text = self.recognizer.recognize_google(audio, language=input_lang_code)
                self.input_text.delete("1.0", tk.END)
                self.input_text.insert(tk.END, input_text)
                self.translate_and_speak(input_text)
            except Exception as e:
                print(f"Error recognizing speech: {e}")

    def get_language_code(self, language_name):
        for code, name in LANGUAGES.items():
            if name.lower() == language_name.lower():
                return code
        return 'en'

    def translate_and_speak(self, text):
        input_lang_code = self.get_language_code(self.input_lang.get())
        output_lang_code = self.get_language_code(self.output_lang.get())
        translated_text = self.translator.translate(text, src=input_lang_code, dest=output_lang_code).text
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert(tk.END, translated_text)
        self.speak_text(translated_text, output_lang_code)

    def speak_text(self, text, lang_code):
        tts = gTTS(text=text, lang=lang_code, slow=False)
        tts.save("output.mp3")
        self.play_audio("output.mp3")

    def play_audio(self, file_path):
        pygame.mixer.init()
        pygame.mixer.music.load(file_path)
        pygame.mixer.music.play()
        while pygame.mixer.music.get_busy():
            time.sleep(0.1)
        pygame.mixer.quit()
        os.remove(file_path)

def fetch_news(url):
    try:
        # Initialize an article object
        article = Article(url)
        
        # Download the article
        article.download()
        
        # Parse the article
        article.parse()
        
        # Perform NLP to extract keywords and summary
        article.nlp()
        
        # Extract and format the publication date
        pub_date = article.publish_date
        if pub_date is not None:
            pub_date = pub_date.strftime('%Y-%m-%d')
        else:
            pub_date = "No date available"
        
        # Extract other details
        title = article.title
        authors = article.authors
        summary = article.summary
        top_image = article.top_image
        keywords = article.keywords
        
        # Return the extracted information
        return {
            'title': title,
            'authors': authors,
            'publication_date': pub_date,
            'summary': summary,
            'top_image': top_image,
            'keywords': keywords
        }
    except Exception as e:
        return {'error': str(e)}

def fetch_top_news():
    site = 'https://news.google.com/news/rss'
    op = urlopen(site)
    rd = op.read()
    op.close()
    sp_page = soup(rd, 'xml')
    news_list = sp_page.find_all('item')
    return news_list

def fetch_recent_news():
    site = 'https://news.google.com/news/rss/headlines/section/topic/WORLD'
    op = urlopen(site)
    rd = op.read()
    op.close()
    sp_page = soup(rd, 'xml')
    news_list = sp_page.find_all('item')
    return news_list

def fetch_cinema_news():
    site = 'https://news.google.com/news/rss/headlines/section/entertainment'
    op = urlopen(site)
    rd = op.read()
    op.close()
    sp_page = soup(rd, 'xml')
    news_list = sp_page.find_all('item')
    return news_list

def fetch_sports_news():
    site = 'https://news.google.com/news/rss/headlines/section/sport'
    op = urlopen(site)
    rd = op.read()
    op.close()
    sp_page = soup(rd, 'xml')
    news_list = sp_page.find_all('item')
    return news_list

def summarize_news(news_list, limit=5):
    summaries = []
    count = 0
    
    for news in news_list:
        if count >= limit:
            break
        news_url = news.link.text
        news_data = fetch_news(news_url)
        if 'error' not in news_data:
            summaries.append(news_data)
            count += 1
    
    return summaries

def display_summaries(summaries, frame):
    for widget in frame.winfo_children():
        widget.destroy()
    
    for idx, news in enumerate(summaries, start=1):
        if news['top_image']:
            try:
                response = requests.get(news['top_image'])
                img_data = response.content
                img = Image.open(BytesIO(img_data))
                img = img.resize((200, 150), Image.LANCZOS)
                photo = ImageTk.PhotoImage(img)
                img_label = tk.Label(frame, image=photo, bg='#e0f7fa')
                img_label.image = photo
                img_label.grid(row=idx, column=0, padx=10, pady=10, sticky='n')
            except Exception as e:
                print(f"Could not load image: {e}")
        
        text_widget = tk.Text(frame, wrap=tk.WORD, width=80, height=15, bg='#f5f5f5', font=('Helvetica', 10))
        text_widget.grid(row=idx, column=1, padx=10, pady=10)
        
        text_widget.insert(tk.END, f"News {idx}:\n", 'title')
        text_widget.insert(tk.END, f"Title: {news['title']}\n", 'heading')
        text_widget.insert(tk.END, f"Authors: {', '.join(news['authors'])}\n", 'text')
        text_widget.insert(tk.END, f"Publication Date: {news['publication_date']}\n", 'text')
        text_widget.insert(tk.END, f"Summary: {news['summary']}\n", 'summary')
        text_widget.insert(tk.END, f"Keywords: {', '.join(news['keywords'])}\n", 'keywords')
        text_widget.insert(tk.END, "\n" + "="*50 + "\n\n", 'separator')
        
        text_widget.config(state=tk.DISABLED)
        text_widget.tag_config('title', font=('Helvetica', 14, 'bold'), foreground='blue')
        text_widget.tag_config('heading', font=('Helvetica', 12, 'bold'), foreground='#D32F2F')
        text_widget.tag_config('text', font=('Helvetica', 10), foreground='#616161')
        text_widget.tag_config('summary', font=('Helvetica', 10, 'italic'), foreground='#388E3C')
        text_widget.tag_config('keywords', font=('Helvetica', 10, 'bold'), foreground='#1976D2')
        text_widget.tag_config('separator', font=('Helvetica', 8), foreground='grey')
        
        # Add a button to read the summary
        read_button = tk.Button(frame, text="Read Summary", command=lambda news=news: read_summary(news['summary']))
        read_button.grid(row=idx, column=2, padx=10, pady=10)

def fetch_and_display_news(news_type, frame):
    if news_type == 'top':
        news_list = fetch_top_news()
    elif news_type == 'recent':
        news_list = fetch_recent_news()
    elif news_type == 'cinema':
        news_list = fetch_cinema_news()
    elif news_type == 'sports':
        news_list = fetch_sports_news()
    news_summaries = summarize_news(news_list, limit=5)
    display_summaries(news_summaries, frame)

def summarize_article(url, frame):
    news_data = fetch_news(url)
    if 'error' not in news_data:
        display_summaries([news_data], frame)
    else:
        messagebox.showerror("Error", "Failed to fetch article")

def read_summary(summary):
    tts = gTTS(text=summary, lang='en', slow=False)
    tts.save("summary.mp3")
    pygame.mixer.init()
    pygame.mixer.music.load("summary.mp3")
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(0.1)
    pygame.mixer.quit()
    os.remove("summary.mp3")

def main():
    root = tk.Tk()
    root.title("News Summarizer")
    root.geometry("1200x800")
    root.configure(bg="#e0f7fa")

    style = ttk.Style()
    style.configure("TFrame", background="#e0f7fa")
    style.configure("TButton", font=("Helvetica", 12), padding=10)
    style.configure("TLabel", background="#e0f7fa", font=("Helvetica", 16, "bold"))

    frame = ttk.Frame(root, padding="10")
    frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

    title_label = ttk.Label(frame, text="News Summarizer", foreground="blue")
    title_label.grid(row=0, column=0, pady=10)

    button_frame = ttk.Frame(frame)
    button_frame.grid(row=1, column=0, pady=5)

    fetch_top_button = tk.Button(button_frame, text="Fetch Top News", command=lambda: fetch_and_display_news('top', news_frame), bg="#4CAF50", fg="white", font=("Helvetica", 12, "bold"))
    fetch_top_button.grid(row=0, column=0, padx=5)

    fetch_recent_button = tk.Button(button_frame, text="Fetch Recent News", command=lambda: fetch_and_display_news('recent', news_frame), bg="#2196F3", fg="white", font=("Helvetica", 12, "bold"))
    fetch_recent_button.grid(row=0, column=1, padx=5)

    fetch_cinema_button = tk.Button(button_frame, text="Fetch Cinema News", command=lambda: fetch_and_display_news('cinema', news_frame), bg="#FF9800", fg="white", font=("Helvetica", 12, "bold"))
    fetch_cinema_button.grid(row=0, column=2, padx=5)

    fetch_sports_button = tk.Button(button_frame, text="Fetch Sports News", command=lambda: fetch_and_display_news('sports', news_frame), bg="#9C27B0", fg="white", font=("Helvetica", 12, "bold"))
    fetch_sports_button.grid(row=0, column=3, padx=5)

    news_frame = ttk.Frame(frame)
    news_frame.grid(row=2, column=0, pady=5)

    url_frame = ttk.Frame(frame)
    url_frame.grid(row=3, column=0, pady=5)

    url_label = ttk.Label(url_frame, text="Enter Article URL: ")
    url_label.grid(row=0, column=0, padx=5)

    url_entry = ttk.Entry(url_frame, width=80)
    url_entry.grid(row=0, column=1, padx=5)

    fetch_article_button = tk.Button(url_frame, text="Summarize Article", command=lambda: summarize_article(url_entry.get(), news_frame), bg="#FF5722", fg="white", font=("Helvetica", 12, "bold"))
    fetch_article_button.grid(row=0, column=2, padx=5)

    root.mainloop()

if __name__ == "__main__":
    main()
