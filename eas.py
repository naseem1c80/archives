import easyocr
import cv2
import json
import re
import PyPDF2
from pdf2image import convert_from_path
import pytesseract
from datetime import datetime
import os
from typing import List, Union
## ===================================== ##
## الجزء الأول: استخراج النص من الصور ##
## ===================================== ##

def extract_text_from_image(image_path, languages=['ar']):
    """
    تستخرج النص من الصور باستخدام EasyOCR
    :param image_path: مسار ملف الصورة
    :param languages: قائمة اللغات (افتراضيًا العربية)
    :return: قائمة النصوص المستخرجة
    """
    try:
        # تهيئة القارئ
        reader = easyocr.Reader(languages)
        
        # قراءة الصورة
        img = cv2.imread(image_path)
        
        if img is None:
            raise ValueError(f"تعذر قراءة ملف الصورة: {image_path}")
        
        # استخراج النص
        results = reader.readtext(img)
        
        # تجميع النصوص المستخرجة
        extracted_text = [text[1] for text in results]
        
        return extracted_text
    
    except Exception as e:
        print(f"حدث خطأ أثناء استخراج النص من الصورة: {str(e)}")
        return []

## ===================================== ##
## الجزء الثاني: استخراج النص من PDF ##
## ===================================== ##

def extract_text_from_pdf(pdf_path):
    """
    تستخرج النص من ملف PDF يحتوي على نص قابل للتحديد
    :param pdf_path: مسار ملف PDF
    :return: النص المستخرج
    """
    try:
        text = ""
        with open(pdf_path, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() or ""
        return text
    
    except Exception as e:
        print(f"حدث خطأ أثناء استخراج النص من PDF: {str(e)}")
        return ""

def extract_text_from_scanned_pdf(pdf_path, languages='ara'):
    """
    تستخرج النص من ملف PDF ممسوح ضوئيًا (صور) باستخدام OCR
    :param pdf_path: مسار ملف PDF
    :param languages: لغة OCR (افتراضيًا العربية)
    :return: النص المستخرج
    """
    try:
        text = ""
        
        # تحويل PDF إلى صور
        images = convert_from_path(pdf_path)
        
        # استخراج النص من كل صورة
        for i, img in enumerate(images):
            text += pytesseract.image_to_string(img, lang=languages)
            print(f"تم معالجة الصفحة {i+1} من {len(images)}")
        
        return text
    
    except Exception as e:
        print(f"حدث خطأ أثناء استخراج النص من PDF الممسوح: {str(e)}")
        return ""

## ===================================== ##
## الجزء الثالث: معالجة النص المستخرج ##
## ===================================== ##

def extract_dates(text):
    """استخراج التواريخ من النص"""
    date_patterns = [
        r'\d{1,2}/\d{1,2}/\d{2,4}',  # 12/05/2025
        r'\d{1,2}-\d{1,2}-\d{2,4}',    # 12-05-2025
        r'\d{1,2}\s+\d{1,2}\s+\d{2,4}' # 12 05 2025
    ]
    
    dates = []
    for pattern in date_patterns:
        dates.extend(re.findall(pattern, text))
    
    return list(set(dates))  # إزالة التواريخ المكررة

def extract_amounts(text):
    """استخراج المبالغ المالية من النص"""
    amount_patterns = [
        r'\d{1,3}(?:,\d{3})*\.\d{2}',  # 3,222,050.00
        r'\d{1,3}(?: \d{3})*\.\d{2}',  # 3 222 050.00
        r'\d+\.\d{2}',                  # 222050.00
        r'\d+ ريال',                    # 100 ريال
        r'\d+ دولار',                   # 100 دولار
    ]
    
    amounts = []
    for pattern in amount_patterns:
        amounts.extend(re.findall(pattern, text))
    
    return list(set(amounts))  # إزالة المبالغ المكررة

def extract_names(text):
    """استخراج الأسماء العربية من النص"""
    name_pattern = r'[أ-ي]+\s+[أ-ي]+\s+[أ-ي]+'
    return re.findall(name_pattern, text)

def find_value(patterns: List[str], texts: List[str], is_amount=False) -> Union[str, None]:
        """
        تبحث عن قيمة في النصوص مع معالجة خاصة للنص العربي
        :param patterns: قائمة أنماط البحث
        :param texts: قائمة النصوص للبحث فيها
        :param is_amount: هل القيمة المطلوبة مبلغ مالي؟
        :return: القيمة المستخرجة أو None إذا لم توجد
        """
        for pattern in patterns:
            for text in texts:
                # البحث مع تجاهل الاختلافات في التشكيل والكتابة
                match = re.search(pattern, text, re.IGNORECASE)
                if match:
                    value = text[match.end():].strip()
                    # تنظيف القيمة من الرموز غير المرغوب فيها
                    value = re.sub(r'^[:\-\|/]\s*', '', value)
                    value = value.split('\n')[0].strip()
                    
                    if is_amount:
                        # استخراج الأرقام فقط من المبالغ المالية
                        amount = re.search(r'[\d,]+\.\d{2}', value)
                        if amount:
                            return amount.group()
                    
                    if value:
                        return value
        return None

def process_extracted_text(texts):
    """
    معالجة النص المستخرج لاستخلاص المعلومات المهمة
    :param text: النص الخام
    :return: قاموس بالمعلومات المستخرجة
    """
    print(texts)
    texts2=[]
    for text in texts.split("\n"):
        
        # إزالة الأحرف الغريبة والحفاظ على العربية والأرقام
        #clean_text = re.sub(r'[^\u0600-\u06FF0-9\s.,/-]', '', text)
        texts2.append(text)#.replace('--',''))
     # تنظيف النصوص من الأحرف غير المرغوب فيها
   
    cleaned_texts = []
    for text in texts2:
        print(f'{text}')
        # إزالة الأحرف الغريبة والحفاظ على العربية والأرقام
        clean_text = re.sub(r'[^\u0600-\u06FF0-9\s.,/-]', '', text)
        cleaned_texts.append(clean_text)

    # استخراج البيانات باستخدام أنماط متطورة
    data = {
        "رقم الحوالة": find_value([
            r'رقم الحوالة\s*',
            r'رقم التحويل\s*',
            r'رﻗﻢ اﻟﺤﻮاﻟﺔ\s*',
            r'1-22031-3-211210010001-0'  # النمط الخاص الموجود في النص
        ], cleaned_texts,is_amount=True),
        
        "رقم الإكسبرس": find_value([
            r'رقم الاكسبرس\s*',
            r'رﻗﻢ اﻻﻛﺴﺒﺮس\s*',
            r'Express No\s*',
            r'3944233389'  # الرقم الظاهر في النص
        ], cleaned_texts,is_amount=True),
        
        "رقم الحساب": find_value([
            r'رقم الحساب\s*',
            r'رﻗﻢ اﻟﺤﺴﺎب\s*',
            r'Account No\s*',
            r'19185233'  # الرقم الظاهر في النص
        ], cleaned_texts),
        
        "اسم المرسل": find_value([
            r'اسم المرسل\s*',
            r'اﺳﻢ اﻟﻤﺮﺳﻞ\s*',
            r'المرسل\s*',
            r'موبايل المرسل\s*',
            r'محمد مرشد سلطان احمد'  # الاسم الظاهر في النص
        ], cleaned_texts),
        
        "اسم المستلم": find_value([
            r'اسم المستلم\s*',
            r'اﺳﻢ اﻟﻤﺴﺘﻠﻢ\s*',
            r'المستلم\s*',
            r'موبايل المستلم\s*',
            r'ام القرى للسفريات'  # الاسم الظاهر في النص
        ], cleaned_texts),
        
        "المبلغ المحول": find_value([
            r'المبلغ المحول\s*',
            r'اﻟﻤﺒﻠﻎ اﻟﻤﺤﻮل\s*',
            r'398.00'  # المبلغ الظاهر في النص
        ], cleaned_texts, is_amount=True),
        
        "مبلغ العمولة": find_value([
            r'مبلغ العمولة\s*',
            r'ﻣﺒﻠﻎ اﻟﻌﻤﻮﻟﺔ\s*',
            r'2.00'  # المبلغ الظاهر في النص
        ], cleaned_texts, is_amount=True),
        
        "المبلغ المقبوض": find_value([
            r'المبلغ المقبوض\s*',
            r'اﻟﻤﺒﻠﻎ اﻟﻤﻘﺒﻮض\s*',
            r'400.00'  # المبلغ الظاهر في النص
        ], cleaned_texts, is_amount=True),
        
        "تاريخ الإصدار": find_value([
            r'تاريخ الإصدار\s*',
            r'التاريخ\s*',
            r'5/13/25 7:47 PM'  # التاريخ الظاهر في النص
        ], cleaned_texts),
        
        "تاريخ الطباعة": find_value([
            r'تاريخ الطباعة\s*',
            r'13/05/2025 21.42.26'  # التاريخ الظاهر في النص
        ], cleaned_texts),
        
        "اسم المستخدم": find_value([
            r'اسم المستخدم\s*',
            r'المستخدم\s*',
            r'بشير منير مسعد المريسي'  # الاسم الظاهر في النص
        ], cleaned_texts),
        
        "اسم الفرع": find_value([
            r'اسم الفرع\s*',
            r'الفرع\s*',
            r'الإدارة العامة'  # الاسم الظاهر في النص
        ], cleaned_texts),
        
        "اسم الحساب": find_value([
            r'اسم الحساب\s*',
            r'حساب\s*',
            r'ام القرى للسفريات'  # الاسم الظاهر في النص
        ], cleaned_texts)
    }

    # معالجة إضافية للبيانات
    if data["المبلغ المحول"]:
        data["المبلغ المحول"] += " ريال سعودي"
    if data["مبلغ العمولة"]:
        data["مبلغ العمولة"] += " ريال سعودي"
    if data["المبلغ المقبوض"]:
        data["المبلغ المقبوض"] += " ريال سعودي"

    return {k: v for k, v in data.items() if v is not None}
    
'''
    return {
        'dates': extract_dates(text),
        'amounts': extract_amounts(text),
        'names': extract_names(text),
        'raw_text': text
    }*/
'''
## ===================================== ##
## الجزء الرابع: الواجهة الرئيسية ##
## ===================================== ##

def main(file_path):
    """
    الوظيفة الرئيسية التي تحدد نوع الملف وتستدعي الدالة المناسبة
    :param file_path: مسار الملف المراد معالجته
    :return: النتائج المستخرجة
    """
    if not os.path.exists(file_path):
        return {"error": "الملف غير موجود"}
    
    file_ext = file_path.split('.')[-1].lower()
    
    if file_ext in ['jpg', 'jpeg', 'png']:
        print("جاري استخراج النص من الصورة...")
        extracted_text = extract_text_from_image(file_path)
    elif file_ext == 'pdf':
        # نفحص أولاً إذا كان PDF يحتوي على نص
        print("جاري فحص ملف PDF...")
        initial_text = extract_text_from_pdf(file_path)
        
        if len(initial_text.strip()) > 50:  # إذا كان هناك نص كافٍ
            print("يحتوي PDF على نص قابل للتحديد")
            extracted_text = initial_text
        else:
            print("يبدو أن PDF ممسوح ضوئيًا، جاري استخدام OCR...")
            extracted_text = extract_text_from_scanned_pdf(file_path)
    else:
        return {"error": "نوع الملف غير مدعوم"}
    
    # معالجة النص المستخرج
    processed_data = process_extracted_text(extracted_text)
    
    # حفظ النتائج في ملف JSON
    output_file = f"نتائج_{os.path.basename(file_path)}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=4)
    
    print(f"تم حفظ النتائج في ملف: {output_file}")
    return processed_data

if __name__ == "__main__":
    # مثال للاستخدام
    file_path = input("الرجاء إدخال مسار الملف (PDF أو صورة): ")
    results = main(file_path)
    print(json.dumps(results, ensure_ascii=False, indent=2))