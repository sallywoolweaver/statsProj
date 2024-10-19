import pdfplumber
import cv2
import numpy as np

pdf_file_path = "stats2.pdf"
output_image_path = "header_boundaries_tuned.png"

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

        # Extract words and boundaries using OCR
        words = page.extract_words()
        field_headers = ["MISSED SHOTS", "GOALS", "FEJ", "Field Blocks", "Steals", "Assists", "TO"]
        goalie_headers = ["Saves", "Goals Allowed", "Shots", "Steals", "Assists", "Faults", "TO"]

        scale_x = image.shape[1] / float(page.width)
        scale_y = image.shape[0] / float(page.height)

        # Track if we are in the goalie section
        goalie_section_started = False

        field_headers_found = {}
        goalie_headers_found = {}

        # First pass: Detect and store field and goalie headers
        for word in words:
            x0 = int(word['x0'] * scale_x)
            y0 = int(word['top'] * scale_y)
            x1 = int(word['x1'] * scale_x)
            y1 = int(word['bottom'] * scale_y)

            word_text_upper = word['text'].strip().upper()

            # If we encounter the word "Goalkeeper", mark the start of the goalie section
            if "GOALKEEPER" in word_text_upper:
                goalie_section_started = True

            # Determine if the word is a field player or goalie header
            if not goalie_section_started and word_text_upper in [header.upper() for header in field_headers]:
                field_headers_found[word_text_upper] = (x0, y0, x1, y1)
                # Draw field player header in red
                cv2.rectangle(image, (x0, y0), (x1, y1), (0, 0, 255), 2)
                cv2.putText(image, word['text'], (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            elif goalie_section_started and word_text_upper in [header.upper() for header in goalie_headers]:
                goalie_headers_found[word_text_upper] = (x0, y0, x1, y1)
                # Draw goalie header in green
                cv2.rectangle(image, (x0, y0), (x1, y1), (0, 255, 0), 2)
                cv2.putText(image, word['text'], (x0, y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)

        # Check for missing headers and estimate their positions more accurately
        def estimate_missing_headers(headers_list, headers_found, section_color, x_gap=70):
            if "GOALS" in headers_found:
                # Use the y-coordinate of the existing "GOALS" header
                goals_y0 = headers_found["GOALS"][1]
                goals_y1 = headers_found["GOALS"][3]

                # Adjust horizontal positions more closely to avoid pushing headers too far to the right
                previous_x1 = headers_found["GOALS"][2]

                for header in headers_list:
                    if header.upper() not in headers_found:
                        # Estimate the x-coordinates for the missing header
                        estimated_x0 = previous_x1 + 10  # Reduced gap for more compact columns
                        estimated_x1 = estimated_x0 + x_gap  # Smaller width estimate for the missing column
                        previous_x1 = estimated_x1

                        # Set the y-coordinates to align with "GOALS"
                        headers_found[header.upper()] = (estimated_x0, goals_y0, estimated_x1, goals_y1)
                        # Draw the estimated header boundary
                        cv2.rectangle(image, (estimated_x0, goals_y0), (estimated_x1, goals_y1), section_color, 2)
                        cv2.putText(image, header, (estimated_x0, goals_y0 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, section_color, 1)

        # Estimate missing field headers (in red)
        estimate_missing_headers(field_headers, field_headers_found, (0, 0, 255), x_gap=60)

        # Estimate missing goalie headers (in green)
        estimate_missing_headers(goalie_headers, goalie_headers_found, (0, 255, 0), x_gap=60)

        # Save the image with drawn boundaries
        cv2.imwrite(output_image_path, image)
        print(f"Image with header boundaries saved to {output_image_path}")

# Run the function to draw header boundaries
draw_header_boundaries(pdf_file_path, output_image_path)
