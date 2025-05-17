import os
from apps.inc.scanner import scan_document
from barcode_reader import read_barcode
from archiver import image_to_pdf
from database import init_db, save_record
from datetime import datetime

# تهيئة المجلدات
os.makedirs("data/scans", exist_ok=True)
os.makedirs("data/archive", exist_ok=True)

# تهيئة قاعدة البيانات
init_db()

# مسح المستند
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
image_path = f"data/scans/scan_{timestamp}.jpg"
pdf_path = f"data/archive/doc_{timestamp}.pdf"

print("جارٍ مسح المستند...")
scan_document(image_path)

print("جارٍ قراءة الباركود...")
barcode = read_barcode(image_path)
if barcode:
    print(f"تم التعرف على الباركود: {barcode}")
else:
    barcode = input("لم يتم التعرف تلقائيًا، أدخل الباركود يدويًا: ")

print("تحويل الصورة إلى PDF...")
image_to_pdf(image_path, pdf_path)

print("تسجيل الأرشيف في قاعدة البيانات...")
save_record(barcode, pdf_path)

print("✅ تم الأرشفة بنجاح!")
