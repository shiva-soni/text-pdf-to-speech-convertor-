import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import pyttsx3
import PyPDF2
import threading
import datetime

is_reading = False
extracted_text = ""
spoken_text = ""

# ================== CORE FUNCTIONS ==================
def select_pdf():
    threading.Thread(target=extract_text_from_pdf).start()

def extract_text_from_pdf():
    global extracted_text
    file_path = filedialog.askopenfilename(filetypes=[("PDF files", "*.pdf")], title="Select a PDF file")

    if not file_path:
        return

    try:
        with open(file_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            total_pages = len(reader.pages)
            page_range = page_entry.get().strip()
            pages_to_read = []

            if page_range:
                parts = page_range.split(',')
                for part in parts:
                    if '-' in part:
                        start, end = map(int, part.split('-'))
                        pages_to_read.extend(range(start - 1, end))
                    else:
                        pages_to_read.append(int(part) - 1)
            else:
                pages_to_read = list(range(total_pages))

            text = ""
            for i in pages_to_read:
                if 0 <= i < total_pages:
                    text += reader.pages[i].extract_text()
                else:
                    root.after(0, lambda i=i: messagebox.showwarning("Warning", f"Page {i + 1} does not exist."))

            if text.strip() == "":
                root.after(0, lambda: messagebox.showerror("Error", "No readable text found!"))
                return

            extracted_text = text
            root.after(0, lambda: update_textbox(extracted_text))
            save_log(file_path)

    except Exception as e:
        root.after(0, lambda: messagebox.showerror("Error", f"Something went wrong:\n{e}"))

def update_textbox(text):
    text_box.delete(1.0, tk.END)
    text_box.insert(tk.END, text)

def save_log(file_path):
    now = datetime.datetime.now()
    with open("log.txt", "a") as f:
        f.write(f"{now.strftime('%Y-%m-%d %H:%M:%S')} - Opened: {file_path}\n")

def speak_text():
    global is_reading, spoken_text
    if is_reading:
        return

    text_to_speak = text_box.get(1.0, tk.END).strip() or extracted_text.strip()
    if not text_to_speak:
        messagebox.showerror("Error", "No text to speak!")
        return

    engine_local = pyttsx3.init()
    voices = engine_local.getProperty('voices')
    selected_voice = voice_var.get()
    if selected_voice == "Male":
        engine_local.setProperty('voice', voices[0].id)
    elif len(voices) > 1:
        engine_local.setProperty('voice', voices[1].id)

    rate = speed_scale.get()
    engine_local.setProperty('rate', rate)

    def speak():
        global is_reading, spoken_text
        is_reading = True
        spoken_text = ""

        text_box.tag_remove("highlight", "1.0", tk.END)
        text_content = text_box.get("1.0", tk.END).strip()
        lines = text_content.split('\n')
        start_line = 1

        for line in lines:
            if not is_reading:
                break
            stripped_line = line.strip()
            if not stripped_line:
                start_line += 1
                continue

            start_index = f"{start_line}.0"
            end_index = f"{start_line}.{len(line)}"
            text_box.tag_remove("highlight", "1.0", tk.END)
            text_box.tag_add("highlight", start_index, end_index)
            text_box.tag_config("highlight", background="#00ff99", foreground="black")
            text_box.see(start_index)
            text_box.update_idletasks()

            spoken_text += stripped_line + " "
            engine_local.say(stripped_line)
            engine_local.runAndWait()

            start_line += 1

        text_box.tag_remove("highlight", "1.0", tk.END)
        is_reading = False

    threading.Thread(target=speak).start()

def stop_speaking():
    global is_reading
    is_reading = False
    text_box.tag_remove("highlight", "1.0", tk.END)

def save_audio():
    if not extracted_text:
        messagebox.showerror("Error", "No text to save!")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("Audio Files", "*.mp3 *.wav")])
    if not file_path:
        return
    try:
        engine_local = pyttsx3.init()
        engine_local.save_to_file(extracted_text, file_path)
        engine_local.runAndWait()
        messagebox.showinfo("Success", "Audio file saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save audio:\n{e}")

def save_spoken_audio():
    if not spoken_text.strip():
        messagebox.showerror("Error", "Nothing has been spoken yet!")
        return
    file_path = filedialog.asksaveasfilename(defaultextension=".mp3", filetypes=[("Audio Files", "*.mp3 *.wav")])
    if not file_path:
        return
    try:
        engine_local = pyttsx3.init()
        engine_local.save_to_file(spoken_text, file_path)
        engine_local.runAndWait()
        messagebox.showinfo("Success", "Spoken audio saved successfully!")
    except Exception as e:
        messagebox.showerror("Error", f"Could not save spoken audio:\n{e}")

# ================== GUI SETUP ==================
root = tk.Tk()
root.title("🟩 PDF to Speech Converter")
root.geometry("850x750")
root.config(bg="#101010")
#root.resizable(False, False)

style_font = ("Segoe UI", 12)

# ========== TITLE ==========
title_label = tk.Label(root, text="PDF to Speech Converter", font=("Segoe UI", 24, "bold"),
                       fg="#00ff99", bg="#101010")
title_label.pack(pady=20)

# ========== FRAME TOP ==========
frame_top = tk.Frame(root, bg="#101010")
frame_top.pack(pady=10)

def create_hover_button(frame, text, cmd, color):
    btn = tk.Button(frame, text=text, command=cmd, font=style_font, bg=color, fg="black",
                    relief="flat", padx=20, pady=5, bd=0, activebackground="#00ff99", activeforeground="black")
    btn.bind("<Enter>", lambda e: btn.config(bg="#00ff99", fg="black"))
    btn.bind("<Leave>", lambda e: btn.config(bg=color, fg="black"))
    return btn

btn_select = create_hover_button(frame_top, "📄 Select PDF", select_pdf, "#00e676")
btn_select.grid(row=0, column=0, padx=10)

tk.Label(frame_top, text="Page Range (e.g. 1-3,5):", font=style_font, bg="#101010", fg="#00ff99").grid(row=0, column=1)
page_entry = tk.Entry(frame_top, width=20, font=style_font, bg="#1b1b1b", fg="#00ff99",
                      insertbackground="#00ff99", relief="flat", bd=3, highlightthickness=1,
                      highlightbackground="#00ff99", highlightcolor="#00ff99")
page_entry.grid(row=0, column=2, padx=10)

# ========== AUDIO CONTROLS ==========
frame_audio = tk.Frame(root, bg="#101010")
frame_audio.pack(pady=15)

btn_play = create_hover_button(frame_audio, "▶ Play", speak_text, "#00c853")
btn_play.grid(row=0, column=0, padx=10)

btn_stop = create_hover_button(frame_audio, "⏹ Stop", stop_speaking, "#00ff99")
btn_stop.grid(row=0, column=1, padx=10)

btn_save_audio = create_hover_button(frame_audio, "💾 Save All Audio", save_audio, "#00e676")
btn_save_audio.grid(row=0, column=2, padx=10)

btn_save_spoken = create_hover_button(frame_audio, "🔊 Save Spoken Part", save_spoken_audio, "#69f0ae")
btn_save_spoken.grid(row=0, column=3, padx=10)

# ========== SPEED & VOICE ==========
speed_label = tk.Label(root, text="Speaking Speed:", font=style_font, bg="#101010", fg="#00ff99")
speed_label.pack()
speed_scale = tk.Scale(root, from_=100, to=300, orient=tk.HORIZONTAL, bg="#101010", fg="#00ff99",
                       troughcolor="#1b1b1b", sliderrelief="flat", highlightthickness=0)
speed_scale.set(200)
speed_scale.pack(pady=5)

voice_label = tk.Label(root, text="Select Voice:", font=style_font, bg="#101010", fg="#00ff99")
voice_label.pack()
voice_var = tk.StringVar(value="Male")
voice_dropdown = ttk.Combobox(root, textvariable=voice_var, values=["Male", "Female"], font=style_font)
voice_dropdown.pack(pady=5)

# ========== TEXT BOX ==========
text_frame = tk.Frame(root, bg="#101010")
text_frame.pack(pady=10)

scrollbar = tk.Scrollbar(text_frame)
scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

text_box = tk.Text(text_frame, wrap=tk.WORD, height=20, width=90, bg="#1b1b1b", fg="#00ff99",
                   font=("Consolas", 11), insertbackground="#00ff99", relief="flat", yscrollcommand=scrollbar.set)
scrollbar.config(command=text_box.yview)
text_box.pack()

# ========== TOGGLE LIGHT MODE ==========
def toggle_mode():
    if root.cget("bg") == "#101010":
        root.config(bg="white")
        title_label.config(bg="white", fg="#00b894")
        frame_top.config(bg="white")
        frame_audio.config(bg="white")
        text_frame.config(bg="white")
        speed_label.config(bg="white", fg="black")
        voice_label.config(bg="white", fg="black")
        toggle_btn.config(text="🌙 Dark Mode", bg="#ddd", fg="black")
        text_box.config(bg="white", fg="black", insertbackground="black")
    else:
        root.config(bg="#101010")
        title_label.config(bg="#101010", fg="#00ff99")
        frame_top.config(bg="#101010")
        frame_audio.config(bg="#101010")
        text_frame.config(bg="#101010")
        speed_label.config(bg="#101010", fg="#00ff99")
        voice_label.config(bg="#101010", fg="#00ff99")
        toggle_btn.config(text="☀ Light Mode", bg="#1b1b1b", fg="#00ff99")
        text_box.config(bg="#1b1b1b", fg="#00ff99", insertbackground="#00ff99")

toggle_btn = tk.Button(root, text="☀ Light Mode", command=toggle_mode,
                       font=style_font, bg="#1b1b1b", fg="#00ff99", relief="flat", padx=20, pady=5)
toggle_btn.pack(pady=10)

root.mainloop()
