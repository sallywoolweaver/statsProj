import pdfplumber
import re

pdf_file_path = "stats2.pdf"

player_stats = {}

# Header bounding boxes (tune these values as needed)
header_boxes = {
    "missed shots": {'x0': 100, 'x1': 150},
    "goals": {'x0': 150, 'x1': 200},
    "fej": {'x0': 200, 'x1': 250},
    "field blocks": {'x0': 250, 'x1': 300},
    "steals": {'x0': 300, 'x1': 350},
    "assists": {'x0': 350, 'x1': 400},
    "turnovers": {'x0': 400, 'x1': 450},
    "ejection 1": {'x0': 450, 'x1': 500},
    "ejection 2": {'x0': 500, 'x1': 550},
    "ejection 3": {'x0': 550, 'x1': 600},
    "to": {'x0': 600, 'x1': 650}
}

def process_player_rows(page):
    global header_boxes
    current_player = None
    current_player_name_parts = []
    words = page.extract_words()

    for word in words:
        text = word['text']
        
        # Match player number followed by name
        if re.match(r"^\d{1,2}$", text):  # Likely a player number
            if current_player_name_parts:
                # Store the previous player
                current_player = " ".join(current_player_name_parts).strip()
                if len(current_player_name_parts) > 1 and current_player not in player_stats:  # Ensure both number and name are present
                    player_stats[current_player] = {key: 0 for key in header_boxes.keys()}
                print(f"Identified Player: {current_player}")
                current_player_name_parts = []

            # Start collecting new player information
            current_player_name_parts.append(text)
        
        elif re.match(r"[A-Z][A-Za-z-]+(?:,?\s+[A-Z][A-Za-z-]+)*", text):  # Likely part of a player's name
            current_player_name_parts.append(text)

        # Process stats for the current player
        if current_player and len(current_player_name_parts) == 0:
            word_x0 = word['x0']
            for category, box in header_boxes.items():
                if box['x0'] <= word_x0 <= box['x1']:
                    tally_count = text.count('|')
                    group_of_five_count = text.count('/') + text.count('\\')
                    total_count = tally_count + group_of_five_count * 5

                    if total_count > 0:
                        player_stats[current_player][category] += total_count
                    elif text.isdigit():
                        player_stats[current_player][category] += int(text)

                    print(f"Player: {current_player}, Category: {category}, Word: {text}, Count: {total_count if total_count > 0 else text}")
                    break

# Extract data from the PDF
with pdfplumber.open(pdf_file_path) as pdf:
    for page_num, page in enumerate(pdf.pages):
        print(f"\nProcessing Page: {page_num + 1}")
        process_player_rows(page)

# Display results
print("\nPlayer Stats:")
for player, stats in player_stats.items():
    print(f"{player}: {stats}")