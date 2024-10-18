import pdfplumber
import cv2
import pytesseract
from pytesseract import Output
import numpy as np
from PIL import Image

pdf_file_path = "stats2.pdf"

def extract_lines_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            print(f"\nProcessing Page: {page_num + 1}")
            pil_image = page.to_image(resolution=300).original

            # Convert the PIL image to a numpy array for OpenCV
            image = np.array(pil_image)

            # Check if the image is valid
            if image is None or image.size == 0:
                print("Error: The image could not be converted properly.")
                continue

            # Convert RGB to BGR (OpenCV uses BGR format)
            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

            # Convert to grayscale
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary_image = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

            # OCR with more lenient configuration
            d = pytesseract.image_to_data(binary_image, output_type=Output.DICT, config="--psm 6")
            field_column_headers = ["MISSED SHOTS", "GOALS", "FEJ", "Steals", "Assists", "TO", "Field Blocks"]
            goalie_column_headers = ["Saves", "Goals Allowed", "Shots", "Steals", "Assists", "Faults", "TO"]
            field_headers_found = {}
            goalie_headers_found = {}

            is_goalie_section = False

            for i, text in enumerate(d["text"]):
                if not text.strip():
                    continue

                # Start processing goalie stats once 'Goalkeeper' is found
                if "Goalkeeper" in text:
                    is_goalie_section = True
                    continue

                # Extract headers for field players (before the goalie section starts)
                if not is_goalie_section:
                    for header in field_column_headers:
                        if header.lower() == text.lower().strip():  # Ensure exact match
                            # Save the field player header with position information
                            field_headers_found[header.lower().replace(" ", "_")] = {
                                "text": text,
                                "x0": d["left"][i],
                                "y0": d["top"][i],
                                "x1": d["left"][i] + d["width"][i],
                                "y1": d["top"][i] + d["height"][i],
                                "line": d["text"][i],
                            }

                # Extract headers for goalies (after the goalie section starts)
                elif is_goalie_section:
                    for header in goalie_column_headers:
                        if header.lower() == text.lower().strip():  # Ensure exact match
                            # Save the goalie header with position information
                            goalie_headers_found[header.lower().replace(" ", "_")] = {
                                "text": text,
                                "x0": d["left"][i],
                                "y0": d["top"][i],
                                "x1": d["left"][i] + d["width"][i],
                                "y1": d["top"][i] + d["height"][i],
                                "line": d["text"][i],
                            }

            # Check for missing headers and estimate their positions for field players
            if "goals" in field_headers_found:
                goals_x0 = field_headers_found["goals"]["x0"]
                goals_y0 = field_headers_found["goals"]["y0"]
                goals_y1 = field_headers_found["goals"]["y1"]

                if "missed_shots" not in field_headers_found:
                    field_headers_found["missed_shots"] = {
                        "text": "MISSED SHOTS",
                        "x0": goals_x0 - 150,  # Estimated position
                        "y0": goals_y0,
                        "x1": goals_x0 - 70,
                        "y1": goals_y1,
                        "line": "MISSED SHOTS",
                    }

                if "fej" not in field_headers_found:
                    field_headers_found["fej"] = {
                        "text": "FEJ",
                        "x0": field_headers_found["goals"]["x1"] + 10,
                        "y0": goals_y0,
                        "x1": field_headers_found["goals"]["x1"] + 80,
                        "y1": goals_y1,
                        "line": "FEJ",
                    }

                if "steals" not in field_headers_found:
                    field_headers_found["steals"] = {
                        "text": "Steals",
                        "x0": field_headers_found["fej"]["x1"] + 10,
                        "y0": goals_y0,
                        "x1": field_headers_found["fej"]["x1"] + 80,
                        "y1": goals_y1,
                        "line": "Steals",
                    }

                if "assists" not in field_headers_found:
                    field_headers_found["assists"] = {
                        "text": "Assists",
                        "x0": field_headers_found["steals"]["x1"] + 10,
                        "y0": goals_y0,
                        "x1": field_headers_found["steals"]["x1"] + 100,
                        "y1": goals_y1,
                        "line": "Assists",
                    }

                if "to" not in field_headers_found:
                    field_headers_found["to"] = {
                        "text": "TO",
                        "x0": field_headers_found["assists"]["x1"] + 10,
                        "y0": goals_y0,
                        "x1": field_headers_found["assists"]["x1"] + 50,
                        "y1": goals_y1,
                        "line": "TO",
                    }

                if "field_blocks" not in field_headers_found:
                    field_headers_found["field_blocks"] = {
                        "text": "Field Blocks",
                        "x0": field_headers_found["to"]["x1"] + 10,
                        "y0": goals_y0,
                        "x1": field_headers_found["to"]["x1"] + 100,
                        "y1": goals_y1,
                        "line": "Field Blocks",
                    }

            print("\nFiltered Field Player Columns of Interest:")
            for header, details in field_headers_found.items():
                print(f"{header}: {details}")

            print("\nFiltered Goalie Columns of Interest:")
            for header, details in goalie_headers_found.items():
                print(f"{header}: {details}")

# Run the function
extract_lines_from_pdf(pdf_file_path)
