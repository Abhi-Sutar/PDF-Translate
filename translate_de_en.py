
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
from src.pdf_translator import translate_pdf
from src.argos_model import ensure_model_installed


def main():
    """
    Main function to create the GUI and handle file selection.
    """
    root = tk.Tk()
    root.withdraw()  # hide root window

    # 1) Pick input PDF
    in_path = filedialog.askopenfilename(
        title="Select German PDF to translate",
        filetypes=[("PDF files", "*.pdf")],
    )
    if not in_path:
        return

    # 2) Pick where to save output
    out_path = filedialog.asksaveasfilename(
        title="Save translated PDF as...",
        defaultextension=".pdf",
        filetypes=[("PDF files", "*.pdf")],
    )
    if not out_path:
        return

    # Create progress window
    progress_win = tk.Toplevel()
    progress_win.title("Translating...")
    tk.Label(progress_win, text="Translation Progress:").pack(padx=10, pady=(10, 0))
    progress_bar = ttk.Progressbar(
        progress_win,
        orient="horizontal",
        length=400,
        mode="determinate"
    )
    progress_bar.pack(padx=10, pady=10)

    try:
        translation = ensure_model_installed()
        translate_pdf(in_path, out_path, translation, progress_bar)
        messagebox.showinfo("Done", f"Translated PDF saved to:\n{out_path}")
    except Exception as e:
        messagebox.showerror("Error", str(e))
    finally:
        progress_win.destroy()


if __name__ == "__main__":
    main()
