# Google Form Auto-Filler

This script automatically fills and submits the Google Form at:
https://docs.google.com/forms/d/e/1FAIpQLScxrgkZSczQo_I7-tYIXjarPnG2vtSCReDhlqd8HlHzXePEPA/viewform

It targets the Multiple Choice field **Name** using its entry ID: `entry.129147722`.

## How to Run

1. **Install requirements**:
   ```bash
   pip install requests
   ```

2. **Run the script**:
   ```bash
   python3 google_form_filler.py --value "Option 1"
   ```
