import pdfplumber
import cv2
import numpy as np

pdf_file_path = "stats2.pdf"
output_image_path = "header_boundaries_improved.png"

def draw_header_boundaries(pdf_path, output_image_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]  # Only handling the first page for simplicity

        # Extract image from the page with higher resolution
        pil_image = page.to_image(resolution=300).original
        image = np.array(pil_image)

        if image is None or image.size == 0:
            print("Error: The image could not be converted properly.")
            return

        # Convert RGB to BGR for OpenCV
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Extract words and boundaries
        words = page.extract_words()
        field_headers = ["MISSED SHOTS", "GOALS", "FEJ", "STEALS", "ASSISTS", "TO", "FIELD BLOCKS"]
        goalie_headers = ["SAVES", "GOALS ALLOWED", "SHOTS", "STEALS", "ASSISTS", "FAULTS", "TO"]

        # Function to perform a forgiving match for headers
        def is_header_match(text, headers):
            text_upper = text.strip().upper()
            for header in headers:
                header_upper = header.upper()
                if text_upper == header_upper:
                    return True
                # Allow partial matches if the text is part of the header or vice versa
                if text_upper in header_upper or header_upper in text_upper:
                    return True
            return False

        for word in words:
            # Scale the coordinates to match image resolution
            scale_x = image.shape[1] / float(page.width)
            scale_y = image.shape[0] / float(page.height)

            x0 = int(word['x0'] * scale_x)
            y0 = int(word['top'] * scale_y)
            x1 = int(word['x1'] * scale_x)
            y1 = int(word['bottom'] * scale_y)

            # Determine if the word is a field player header or goalie header
            if is_header_match(word['text'], field_headers):
                # Draw rectangle around each field header in red
                cv2.rectangle(image, (x0, y0), (x1, y1), (0, 0, 255), 2)
                cv2.putText(image, word['text'], (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)
            elif is_header_match(word['text'], goalie_headers):
                # Draw rectangle around each goalie header in green
                cv2.rectangle(image, (x0, y0), (x1, y1), (0, 255, 0), 2)
                cv2.putText(image, word['text'], (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Save the image with drawn boundaries
        cv2.imwrite(output_image_path, image)
        print(f"Image with header boundaries saved to {output_image_path}")

# Run the function to draw header boundaries
draw_header_boundaries(pdf_file_path, output_image_path)
