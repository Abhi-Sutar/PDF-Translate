#!/usr/bin/env python3
"""
translate_de_en_with_progress.py

A GUI to pick a German PDF, translate it to English via Argos Translate,
and show a progress bar during translation while preserving formatting.
"""


import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk

import fitz  # PyMuPDF
from argostranslate import package, translate




def ensure_model_installed(from_code="de", to_code="en"):
    """
    Downloads (if needed) the Argos model for de→en
    and returns the Translation object.
    """
    package.update_package_index()
    available_packages = package.get_available_packages()
    pkg = next(
        (p for p in available_packages if p.from_code == from_code and p.to_code == to_code),
        None
    )
    if pkg is None:
        raise RuntimeError(f"No Argos model available for {from_code}→{to_code}")
    model_path = pkg.download()
    package.install_from_path(model_path)
    langs = translate.get_installed_languages()
    src = next(l for l in langs if l.code == from_code)
    dst = next(l for l in langs if l.code == to_code)
    return src.get_translation(dst)


def translate_pdf(input_path, output_path, translation, progress_bar):
    """
    Translate each page and update the progress bar while preserving formatting.
    """
    pdf_document = fitz.open(input_path)
    total_pages = len(pdf_document)
    progress_bar['maximum'] = total_pages

    # Create a new PDF for the translated content
    translated_pdf = fitz.open()

    for idx, page in enumerate(pdf_document, start=1):
        # Extract text from the page
        text = page.get_text("text") or ""
        eng = translation.translate(text)

        # Create a new page with the same dimensions as the original
        new_page = translated_pdf.new_page(width=page.rect.width, height=page.rect.height)

        # Add the translated text to the new page
        new_page.insert_text((50, 50), eng, fontsize=12, color=(0, 0, 0))

        # Update progress bar
        progress_bar['value'] = idx
        progress_bar.update()

    # Save the translated PDF
    translated_pdf.save(output_path)
    translated_pdf.close()
    pdf_document.close()


def main():
    """
    Main function to create the GUI and handle file selection.
    """
    root = tk.Tk()
    root.withdraw()  # hide root window

    # 1) Pick input PDF
    in_path = filedialog.askopenfilename(
        title="Select German PDF to translate",
        filetypes=[("PDF files","*.pdf")],
    )
    if not in_path:
        return

    # 2) Pick where to save output
    out_path = filedialog.asksaveasfilename(
        title="Save translated PDF as...",
        defaultextension=".pdf",
        filetypes=[("PDF files","*.pdf")],
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
