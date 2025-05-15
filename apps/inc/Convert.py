from pdf2image import convert_from_path
import os
import uuid

def convert_pdf_to_images(pdf_path, output_folder='static/converted_images'):
    # تأكد من وجود مجلد الإخراج
    os.makedirs(output_folder, exist_ok=True)

    # تحويل الصفحات
    images = convert_from_path(pdf_path, dpi=200)

    image_paths = []
    for i, image in enumerate(images):
        filename = f"{uuid.uuid4()}.png"
        full_path = os.path.join(output_folder, filename)
        image.save(full_path, 'PNG')
        image_paths.append(full_path)

    return image_paths
