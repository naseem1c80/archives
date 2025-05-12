from PIL import Image
import os

def image_to_pdf(image_path, pdf_path):
    img = Image.open(image_path).convert("RGB")
    img.save(pdf_path)
    return pdf_path
