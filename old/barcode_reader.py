from pyzbar.pyzbar import decode
from PIL import Image

def read_barcode(image_path):
    img = Image.open(image_path)
    decoded = decode(img)
    if not decoded:
        return None
    return decoded[0].data.decode("utf-8")
