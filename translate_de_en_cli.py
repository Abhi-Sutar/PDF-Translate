import argparse
import traceback
from src.pdf_translator import translate_pdf
from src.argos_model import ensure_model_installed


def main():
    """
    Command-line interface for translating PDFs.
    """
    parser = argparse.ArgumentParser(description="Translate a German PDF to English.")
    parser.add_argument("input", help="Path to the input PDF file")
    parser.add_argument("output", help="Path to save the translated PDF file")
    args = parser.parse_args()

    try:
        print("Ensuring translation model is installed...")
        translation = ensure_model_installed()
        print("Translating PDF...")
        translate_pdf(args.input, args.output, translation)
        print(f"Translation complete. Translated PDF saved to: {args.output}")
    except Exception as e:
        print("An error occurred:")
        traceback.print_exc()  # Print the full stack trace


if __name__ == "__main__":
    main()