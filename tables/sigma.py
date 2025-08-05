import os
import re

# Set the directory containing your files
directory = '/home/karankamath/Desktop/Alfatools Data Extraction/tables'  # Change this to your actual directory

# Regex pattern to match {something}-Page-{some-number}.csv
pattern = re.compile(r'^(.+)-Page-(\d+)\.csv$')

for filename in os.listdir(directory):
    match = pattern.match(filename)
    if match:
        something = match.group(1)
        page_number = match.group(2)
        new_filename = f'Page-{page_number}-{something}.csv'

        old_path = os.path.join(directory, filename)
        new_path = os.path.join(directory, new_filename)

        os.rename(old_path, new_path)
        print(f'Renamed: {filename} → {new_filename}')

