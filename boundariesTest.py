import pdfplumber
import cv2
import numpy as np

pdf_file_path = "stats2.pdf"
output_image_path = "header_boundaries_dynamic_corrected.png"

def draw_header_boundaries(pdf_path, output_image_path):
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[0]  # Handling the first page for simplicity

        # Extract image from the page with higher resolution
        pil_image = page.to_image(resolution=300).original
        image = np.array(pil_image)

        if image is None or image.size == 0:
            print("Error: The image could not be converted properly.")
            return

        # Convert RGB to BGR for OpenCV
        image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

        # Extract words and boundaries using OCR
        words = page.extract_words()

        # Define the field and goalie headers in known order
        field_headers_order = ["MISSED SHOTS", "GOALS", "FEJ", "Field Blocks", "Steals", "Assists", "TO"]
        goalie_headers_order = ["Saves", "Goals Allowed", "Shots", "Steals", "Assists", "Faults", "TO"]

        # Scaling factors for coordinates
        scale_x = image.shape[1] / float(page.width)
        scale_y = image.shape[0] / float(page.height)

        # Variables to store detected headers and anchor lines
        field_headers_detected = {}
        goalie_headers_detected = {}
        field_y_anchor = None
        goalie_y_anchor = None
        goalie_section_started = False

        # First Pass: Identify headers and set y-axis anchors for field and goalie sections
        for word in words:
            x0 = int(word['x0'] * scale_x)
            y0 = int(word['top'] * scale_y)
            x1 = int(word['x1'] * scale_x)
            y1 = int(word['bottom'] * scale_y)

            word_text_upper = word['text'].strip().upper()

            # Debug: Print out the detection of each header and its coordinates
            if word_text_upper in [label.upper() for label in (field_headers_order + goalie_headers_order)]:
                print(f"Detected '{word_text_upper}' at x0: {x0}, y0: {y0}, x1: {x1}, y1: {y1}")

            # Detect the start of the goalie section
            if "GOALKEEPER" in word_text_upper:
                goalie_section_started = True

            # Match headers for field players before the goalie section starts
            if not goalie_section_started:
                for header in field_headers_order:
                    if header.upper() == word_text_upper:
                        # Set the y-axis anchor if it's not already set
                        if field_y_anchor is None or abs(y0 - field_y_anchor) < 10:  # Use the most consistent y
                            field_y_anchor = y0
                        # Save the field header
                        field_headers_detected[header] = {
                            'x0': x0,
                            'y0': y0,
                            'x1': x1,
                            'y1': y1
                        }

            # Match headers for goalies after the goalie section starts
            else:
                for header in goalie_headers_order:
                    if header.upper() == word_text_upper:
                        # Set the y-axis anchor if it's not already set
                        if goalie_y_anchor is None:
                            goalie_y_anchor = y0
                        # Save the goalie header
                        goalie_headers_detected[header] = {
                            'x0': x0,
                            'y0': y0,
                            'x1': x1,
                            'y1': y1
                        }

        # Assign headers consistently along the anchor y-axis, using detected coordinates first
        def assign_headers(headers_order, detected_headers, anchor_y, section_color):
            current_x = None
            header_height = 25  # Estimated height of the header box

            for header in headers_order:
                if header in detected_headers:
                    # Use detected coordinates for accuracy if they align with the anchor y
                    header_info = detected_headers[header]
                    x0, y0, x1, y1 = header_info['x0'], anchor_y, header_info['x1'], anchor_y + header_height
                else:
                    # Estimate the position for missing labels using the previous header's position
                    if current_x is not None:
                        x0 = current_x + 10
                        y0 = anchor_y
                        x1 = x0 + 90
                        y1 = anchor_y + header_height
                    else:
                        # If no current_x is available (missing "GOALS" as an anchor), start at an arbitrary position
                        x0 = 50
                        y0 = anchor_y
                        x1 = x0 + 90
                        y1 = anchor_y + header_height

                # Debug: Print out the drawing coordinates for each header
                print(f"Drawing '{header}' boundary at x0: {x0}, y0: {y0}, x1: {x1}, y1: {y1}")

                # Draw the detected or estimated header at the fixed y-axis
                cv2.rectangle(image, (x0, y0), (x1, y1), section_color, 2)
                cv2.putText(image, header, (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, section_color, 1)

                current_x = x1  # Update the current x to draw the next label in sequence

        # Draw field headers (red) using the detected field y-axis anchor
        if field_y_anchor is not None:
            assign_headers(field_headers_order, field_headers_detected, field_y_anchor, (0, 0, 255))  # Red for field headers

        # Draw goalie headers (green) using the detected goalie y-axis anchor
        if goalie_y_anchor is not None:
            assign_headers(goalie_headers_order, goalie_headers_detected, goalie_y_anchor, (0, 255, 0))  # Green for goalie headers

        # Save the image with drawn boundaries
        cv2.imwrite(output_image_path, image)
        print(f"Image with header boundaries saved to {output_image_path}")

# Run the function to draw header boundaries
draw_header_boundaries(pdf_file_path, output_image_path)
