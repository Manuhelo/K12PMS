# procurement/utils.py

import barcode
from barcode.writer import ImageWriter
import os

def generate_po_barcode(po_number, folder='media/barcodes'):
    os.makedirs(folder, exist_ok=True)  # Create folder if not exist
    CODE128 = barcode.get_barcode_class('code128')
    barcode_obj = CODE128(po_number, writer=ImageWriter())
    file_path = os.path.join(folder, f"{po_number}")
    return barcode_obj.save(file_path)  # Returns full path



