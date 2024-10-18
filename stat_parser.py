import pdfplumber
import cv2
import pytesseract
from pytesseract import Output
import numpy as np
from PIL import Image

pdf_file_path = "stats2.pdf"

# Players' names and Y-coordinates already extracted
def extract_player_names_and_y_coordinates(pdf_path):
    players = []
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            words = page.extract_words()  # Extract all words from the page
            for i, word in enumerate(words):
                if ',' in word['text']:  # Assuming player names contain a comma (e.g., "Last, First")
                    player_number = words[i - 1]['text'] if i > 0 and words[i - 1]['text'].isdigit() else "Unknown"
                    player_name = word['text']
                    players.append({'name': player_name, 'number': player_number, 'y_coord': word['top']})
    return players


def extract_missed_shots(pdf_path, players, column_coords):
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            pil_image = page.to_image(resolution=300).original
            image = np.array(pil_image)
            if image is None or image.size == 0:
                print("Error: The image could not be converted properly.")
                continue

            image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            _, binary_image = cv2.threshold(gray, 128, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

            for player in players:
                y_coord = player['y_coord']
                x0, x1 = column_coords['missed_shots']['x0'], column_coords['missed_shots']['x1']
                cropped_image = binary_image[int(y_coord - 5):int(y_coord + 15), x0:x1]
                markings = pytesseract.image_to_string(cropped_image, config='--psm 10').strip()
                print(f"Player: {player['name']}, Missed Shots: {markings}")


# Example usage
players = extract_player_names_and_y_coordinates(pdf_file_path)
column_coords = {
    "missed_shots": {"x0": 507, "x1": 587}
}
extract_missed_shots(pdf_file_path, players, column_coords)
