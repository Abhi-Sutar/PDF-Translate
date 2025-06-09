import fitz  # PyMuPDF
from tqdm import tqdm  # For command-line progress bar


def normalize_color(color):
    """
    Normalize color values to the range [0, 1].
    """
    try:
        # Handle tuple case (RGB or RGBA)
        if isinstance(color, tuple) and len(color) in [3, 4]:
            # For extreme values, apply stronger normalization
            if any(c > 256 for c in color):
                # Find the maximum value and use it as the divisor
                max_val = max(color)
                if max_val > 0:
                    return tuple(float(c) / max_val for c in color)
            # For normal range values
            return tuple(float(c) / 255.0 if c > 1.0 else float(c) for c in color)
        
        # Handle int/float case (grayscale)
        elif isinstance(color, (int, float)):
            if color > 256:
                return (1.0, 1.0, 1.0)  # If extremely large, just use white
            normalized = float(color) / 255.0 if color > 1.0 else float(color)
            return (normalized, normalized, normalized)
        
        # Handle other cases
        else:
            print(f"Warning: Invalid color value type: {type(color)}, value: {color}")
            return (0.0, 0.0, 0.0)  # Default to black
    except Exception as e:
        print(f"Error normalizing color: {color}, Exception: {e}")
        return (0.0, 0.0, 0.0)  # Default to black on error


def translate_pdf(input_path, output_path, translation, progress_bar=None):
    """
    Translate each page and update the progress bar while preserving formatting.
    """
    pdf_document = fitz.open(input_path)
    total_pages = len(pdf_document)
    
    # Create a new PDF for the translated content
    translated_pdf = fitz.open()

    # Define a fallback font file
    fallback_font_path = "C:/Windows/Fonts/arial.ttf"
    
    # Use tqdm for command line progress tracking if no GUI progress bar provided
    if progress_bar is None:
        pages_iter = tqdm(enumerate(pdf_document, start=1), total=total_pages, desc="Translating pages")
    else:
        progress_bar['maximum'] = total_pages
        pages_iter = enumerate(pdf_document, start=1)

    # Debug counter for text segments processed
    text_count = 0
    
    for idx, page in pages_iter:
        # Get page dimensions to constrain text width
        page_width = page.rect.width
        page_margin = 20  # Margin in points to prevent text hitting the edge
        max_text_width = page_width - 2 * page_margin
        
        # Create a new page with the same dimensions as the original
        new_page = translated_pdf.new_page(width=page.rect.width, height=page.rect.height)
        
        # Get the full page dict that contains all text elements
        page_dict = page.get_text("dict")
        
        # First, handle standalone headers and form-type text (often at the top)
        for block in page_dict["blocks"]:
            if "lines" in block:
                # Look for header-like blocks (typically have fewer lines and larger font)
                is_header = len(block["lines"]) <= 3  # Headers typically have 1-3 lines
                
                for line in block["lines"]:
                    # Extract and process each text span in the line
                    for span in line["spans"]:
                        x0, y0, x1, y1 = span["bbox"]
                        text = span["text"].strip()
                        font_size = span["size"]
                        
                        # Headers and form fields often have these characteristics
                        is_form_field = (y0 < page.rect.height * 0.2)  # In top 20% of page
                        is_standalone = (len(text) < 50)  # Short text
                        
                        if text and (is_header or is_form_field or is_standalone):
                            translated_text = translation.translate(text)
                            text_count += 1
                            
                            # Increase width slightly for headers to accommodate longer translations
                            width_factor = 1.5 if is_header or is_standalone else 1.2
                            width = min((x1 - x0) * width_factor, max_text_width)
                            
                            # Create a rectangle for the text with some padding
                            text_rect = fitz.Rect(x0, y0, x0 + width, y1 + 20)
                            
                            # Insert the translated text
                            new_page.insert_textbox(
                                text_rect,
                                translated_text,
                                fontname="helv",
                                fontsize=font_size,
                                color=(0, 0, 0),
                                align=0  # Left-aligned
                            )
        
        # Now process the main content using the word-extraction approach
        words = page.get_text("words")
        
        # Track which words we've already processed as headers/form fields
        processed_positions = set()
        
        # Group words into larger text chunks for better translation
        chunks = []
        current_chunk = []
        last_y = -1
        last_block = -1
        
        for word in words:
            x0, y0, x1, y1, text, block_no, line_no, word_no = word
            
            # Skip words that are part of headers we already processed
            position_key = f"{x0:.1f}_{y0:.1f}"
            if position_key in processed_positions:
                continue
                
            # If we're on a new line or block and have accumulated text, add it to chunks
            if (last_y != -1 and (abs(y0 - last_y) > 5 or block_no != last_block)) and current_chunk:
                chunks.append((current_chunk[0][0], current_chunk[0][1], 
                              current_chunk[-1][2], current_chunk[-1][3], 
                              " ".join(w[4] for w in current_chunk)))
                current_chunk = []
            
            current_chunk.append(word)
            last_y = y0
            last_block = block_no
        
        # Add the last chunk
        if current_chunk:
            chunks.append((current_chunk[0][0], current_chunk[0][1], 
                          current_chunk[-1][2], current_chunk[-1][3], 
                          " ".join(w[4] for w in current_chunk)))
        
        # Process chunks for translation
        for x0, y0, x1, y1, text in chunks:
            if text.strip():
                text_count += 1
                translated_text = translation.translate(text)
                
                # Calculate text width and adjust placement
                text_width = min(x1 - x0, max_text_width)
                
                # Use textbox to enable text wrapping
                text_rect = fitz.Rect(x0, y0, x0 + text_width, y1 + 20)  # Extra height for potential wrapping
                
                # Insert text with wrapping enabled
                new_page.insert_textbox(
                    text_rect,
                    translated_text,
                    fontname="helv",  # Use a built-in PDF font for better compatibility
                    fontsize=11,
                    color=(0, 0, 0),
                    align=0  # 0=left, 1=center, 2=right
                )
        
        # Copy over any images
        for img in page.get_images(full=True):
            xref = img[0]  # get the XREF of the image
            try:
                pix = fitz.Pixmap(pdf_document, xref)
                
                # Calculate the image position and size (use image bounding box if possible)
                for block in page_dict["blocks"]:
                    if "image" in block and block.get("number", -1) == xref:
                        img_rect = fitz.Rect(block["bbox"])
                        new_page.insert_image(img_rect, pixmap=pix)
                        break
            except Exception as e:
                print(f"Error handling image: {e}")
        
        # Update GUI progress bar if provided
        if progress_bar:
            progress_bar['value'] = idx
            progress_bar.update()

    print(f"Processed {text_count} text segments across {total_pages} pages")
    
    # Save the translated PDF
    translated_pdf.save(output_path)
    translated_pdf.close()
    pdf_document.close()