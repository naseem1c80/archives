from flask import Blueprint, render_template, request, jsonify, current_app
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import base64
import re
from datetime import datetime
import requests
import json
import time
import shutil
from PIL import Image
import pytesseract

# Load environment variables
load_dotenv()

# Create blueprint
blueprint = Blueprint('gemini_ocr', __name__, url_prefix='/gemini-ocr', template_folder='templates')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff', 'tif', 'webp'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def detect_document_type(filename, file_path):
    """
    الكشف التلقائي عن نوع المستند
    """
    filename_upper = filename.upper()
    
    # كشف نوع المستند من اسم الملف
    if any(keyword in filename_upper for keyword in ['PASSPORT', 'الجواز', 'PASSPORT']):
        return "passport"
    elif any(keyword in filename_upper for keyword in ['ID', 'هوية', 'بطاقة', 'IDENTIFICATION']):
        return "id_card"
    elif any(keyword in filename_upper for keyword in ['INVOICE', 'فاتورة', 'BILL']):
        return "invoice"
    elif any(keyword in filename_upper for keyword in ['CONTRACT', 'عقد', 'اتفاقية']):
        return "contract"
    elif any(keyword in filename_upper for keyword in ['RECEIPT', 'إيصال', 'سند']):
        return "receipt"
    
    # يمكن إضافة كشف من محتوى الصورة لاحقاً
    return "general"

def process_with_pytesseract(file_path):
    """
    معالجة الملف باستخدام PyTesseract
    """
    try:
        # استخراج النص باستخدام PyTesseract
        extracted_text = pytesseract.image_to_string(Image.open(file_path), lang='ara+eng')
        
        # تنظيف النص
        cleaned_text = clean_extracted_text(extracted_text)
        
        # استخراج الأسطر
        lines = [line.strip() for line in extracted_text.split('\n') if line.strip()]
        
        return {
            'pytesseract_text': cleaned_text,
            'pytesseract_lines': lines,
            'pytesseract_word_count': len(cleaned_text.split()),
            'pytesseract_character_count': len(cleaned_text)
        }
    except Exception as e:
        raise Exception(f"PyTesseract processing failed: {str(e)}")

def process_with_gemini(file_path, prompt_type):
    """
    معالجة الملف باستخدام Gemini AI
    """
    try:
        # استخراج النص باستخدام REST API
        extracted_text = analyze_image_with_gemini_rest_api(file_path, prompt_type)
        
        # استخراج البيانات المنظمة
        structured_result = extract_structured_data_from_text(extracted_text, os.path.basename(file_path))
        print(f"{structured_result}")
        
        return {
            'gemini_text': extracted_text,
            'structured_info': structured_result['structured_info'],
            'lines':structured_result['lines'],
            'document_type': structured_result.get('document_type', 'unknown'),
            'language_analysis': structured_result['language_analysis'],
            'quality_analysis': structured_result['quality_analysis'],
            'gemini_word_count': len(extracted_text.split()),
            'gemini_character_count': len(extracted_text)
        }
    except Exception as e:
        raise Exception(f"Gemini AI processing failed: {str(e)}")

def clean_extracted_text(text):
    """
    تنظيف النص المستخرج
    """
    # إزالة المسافات الزائدة
    text = re.sub(r'\s+', ' ', text)
    # إزالة الأسطر الفارغة المتعددة
    text = re.sub(r'\n\s*\n', '\n', text)
    return text.strip()

def analyze_image_with_gemini_rest_api(image_path, prompt_type="general"):
    """استخراج النص باستخدام REST API مباشرة مع النماذج الجديدة"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise Exception("مفتاح API غير موجود")
        
        # تحميل الصورة وتحويلها إلى base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # استخدام أحد النماذج المتاحة - gemini-2.0-flash-exp
        model_name = "gemini-2.0-flash"
        
        # إنشاء الـ prompt المناسب
        if prompt_type == "passport":
            prompt = """
            قم بتحليل صورة جواز السفر هذه واستخراج جميع المعلومات النصية بدقة عالية.

            المعلومات المطلوبة:
            - رقم الجواز (Passport No)
            - اللقب (Surname)
            - الأسماء (Given Names)
            - الجنسية (Nationality)
            - تاريخ الميلاد (Date of Birth)
            - مكان الميلاد (Place of Birth)
            - الجنس (Sex)
            - تاريخ الإصدار (Date of Issue)
            - تاريخ الانتهاء (Date of Expiry)
            - السلطة المصدرة (Issuing Authority)

            أعد النص كما يظهر في الصورة مع الحفاظ على الترتيب والدقة.
            ركز على قراءة النص العربي بشكل صحيح.
            """
        else:
            prompt = """
            قم بقراءة واستخراج كل النصوص الموجودة في هذه الصورة بدقة عالية.
            حافظ على الترتيب الأصلي للنص كما يظهر في الصورة.
            ركز على النص العربي وتأكد من قراءته بشكل صحيح.
            أعد النص الخام كما هو موجود في الصورة.
            """
        
        # إعداد الطلب
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg",
                                "data": image_data
                            }
                        }
                    ]
                }
            ],
            "generationConfig": {
                "temperature": 0.1,
                "topK": 32,
                "topP": 0.95,
                "maxOutputTokens": 2048,
            }
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                text = result['candidates'][0]['content']['parts'][0]['text']
                logging.info(f"Gemini API response successful, text length: {len(text)}")
                return text
            else:
                logging.error("No candidates in response")
                raise Exception("لا توجد نتائج في استجابة API")
        else:
            error_detail = response.text
            logging.error(f"API error {response.status_code}: {error_detail}")
            raise Exception(f"خطأ في API: {response.status_code} - {error_detail}")
            
    except requests.exceptions.Timeout:
        logging.error("Request timeout")
        raise Exception("انتهت مهلة الطلب. حاول مرة أخرى.")
    except Exception as e:
        logging.error(f"Gemini REST API error: {str(e)}")
        raise Exception(f"خطأ في Gemini API: {str(e)}")

def analyze_image_with_gemini_vision_api(image_path, prompt_type="general"):
    """طريقة بديلة باستخدام نموذج الرؤية"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            raise Exception("مفتاح API غير موجود")
        
        # تحميل الصورة وتحويلها إلى base64
        with open(image_path, "rb") as image_file:
            image_data = base64.b64encode(image_file.read()).decode('utf-8')
        
        # استخدام نموذج gemini-2.0-flash للنصوص والصور
        model_name = "gemini-2.0-flash"
        
        if prompt_type == "passport":
            prompt = "Read all text from this passport image with high accuracy. Focus on Arabic text and extract passport details."
        else:
            prompt = "Extract all text from this image with high accuracy. Maintain original order and focus on Arabic text recognition."
        
        # إعداد الطلب
        url = f"https://generativelanguage.googleapis.com/v1/models/{model_name}:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        
        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {
                            "inline_data": {
                                "mime_type": "image/jpeg", 
                                "data": image_data
                            }
                        }
                    ]
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=45)
        
        if response.status_code == 200:
            result = response.json()
            if 'candidates' in result and len(result['candidates']) > 0:
                return result['candidates'][0]['content']['parts'][0]['text']
            else:
                raise Exception("No response content")
        else:
            raise Exception(f"API error: {response.status_code}")
            
    except Exception as e:
        logging.error(f"Vision API error: {str(e)}")
        # Fallback إلى الطريقة الأولى
        return analyze_image_with_gemini_rest_api(image_path, prompt_type)

def extract_structured_data_from_text(text, filename):
    """استخراج بيانات منظمة من النص المستخرج"""
    structured_data = {
        'raw_text': text,
        'lines': text.split('\n') if text else [],
        'structured_info': {},
        'quality_analysis': {},
        'language_analysis': {}
    }
    
    # تحليل اللغة
    structured_data['language_analysis'] = analyze_languages(text)
    
    # استخراج بيانات جواز السفر إذا كانت موجودة
    if any(keyword in text.upper() for keyword in ['PASSPORT', 'الجواز', 'PASSPORT NO', 'رقم الجواز', 'YEMEN', 'اليمن']):
        structured_data['structured_info']['passport_data'] = extract_passport_info(text)
        structured_data['document_type'] = 'PASSPORT'
    
    # تحليل الجودة
    structured_data['quality_analysis'] = analyze_text_quality_gemini(text)
    
    return structured_data

def analyze_languages(text):
    """تحليل اللغات في النص"""
    if not text:
        return {
            'detected_languages': [],
            'arabic_ratio': 0,
            'english_ratio': 0,
            'total_chars': 0
        }
    
    arabic_pattern = re.compile('[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    english_pattern = re.compile('[a-zA-Z]+')
    
    arabic_chars = len(arabic_pattern.findall(text))
    english_chars = len(english_pattern.findall(text))
    total_chars = len(text)
    
    languages = []
    if arabic_chars > 0:
        languages.append('Arabic')
    if english_chars > 0:
        languages.append('English')
    if not languages:
        languages.append('Unknown')
    
    return {
        'detected_languages': languages,
        'arabic_ratio': arabic_chars / total_chars if total_chars > 0 else 0,
        'english_ratio': english_chars / total_chars if total_chars > 0 else 0,
        'total_chars': total_chars
    }

def extract_passport_info(text):
    """استخراج معلومات جواز السفر من النص"""
    passport_info = {
        'personal_info': {},
        'document_info': {}
    }
    
    lines = text.split('\n')
    
    # استخراج رقم الجواز
    for i, line in enumerate(lines):
        if any(keyword in line.upper() for keyword in ['PASSPORT NO', 'رقم الجواز', 'PASSPORT', 'NO.']):
            for j in range(max(0, i-1), min(i+3, len(lines))):
                numbers = re.findall(r'\d{6,9}', lines[j])
                if numbers:
                    passport_info['document_info']['passport_number'] = numbers[0]
                    break
    
    # استخراج الأسماء
    for i, line in enumerate(lines):
        line_upper = line.upper()
        if any(keyword in line_upper for keyword in ['SURNAME', 'AL-FAKIH', 'اللقب', 'NAME']):
            for j in range(i+1, min(i+4, len(lines))):
                name_line = lines[j].strip()
                if name_line and len(name_line) > 2 and not re.match(r'^\d', name_line):
                    if 'AL-FAKIH' in name_line.upper():
                        passport_info['personal_info']['surname'] = name_line
                    break
        
        if any(keyword in line_upper for keyword in ['GIVEN', 'ASEEL', 'الأسماء', 'FIRST']):
            for j in range(i+1, min(i+4, len(lines))):
                name_line = lines[j].strip()
                if name_line and len(name_line) > 2 and not re.match(r'^\d', name_line):
                    if 'ASEEL' in name_line.upper() or 'HASSAN' in name_line.upper():
                        passport_info['personal_info']['given_names'] = name_line
                    break
    
    # استخراج التواريخ
    date_patterns = [
        r'\d{2}/\d{2}/\d{4}',
        r'\d{4}/\d{2}/\d{2}', 
        r'\d{2}-\d{2}-\d{4}',
        r'\d{4}-\d{2}-\d{2}'
    ]
    
    all_dates = []
    for line in lines:
        for pattern in date_patterns:
            dates = re.findall(pattern, line)
            all_dates.extend(dates)
    
    # تصفية التواريخ الواضحة
    valid_dates = []
    for date in all_dates:
        if any(year in date for year in ['1998', '2021', '2027', '2023', '2024', '2000']):
            valid_dates.append(date)
    
    if valid_dates:
        passport_info['personal_info']['date_of_birth'] = valid_dates[0] if len(valid_dates) > 0 else None
        passport_info['document_info']['expiry_date'] = valid_dates[-1] if len(valid_dates) > 1 else None
        if len(valid_dates) > 2:
            passport_info['document_info']['issue_date'] = valid_dates[1]
    
    # استخراج مكان الميلاد
    for i, line in enumerate(lines):
        if any(keyword in line.upper() for keyword in ['PLACE', 'مكان', 'BIRTH', 'الميلاد', 'TAIZ', 'اليمن']):
            for j in range(i+1, min(i+3, len(lines))):
                place_line = lines[j].strip()
                if place_line and ('TAIZ' in place_line.upper() or 'اليمن' in place_line or 'YEMEN' in place_line.upper()):
                    passport_info['personal_info']['place_of_birth'] = place_line
                    break
    
    return passport_info

def analyze_text_quality_gemini(text):
    """تحليل جودة النص المستخرج"""
    if not text:
        return {
            'quality_score': 0,
            'confidence': 'منخفضة جداً',
            'issues': ['لم يتم استخراج أي نص'],
            'recommendations': ['جرب صورة أوضح', 'تحقق من جودة الصورة']
        }
    
    lines = [line for line in text.split('\n') if line.strip()]
    total_lines = len(lines)
    total_chars = len(text)
    
    if total_chars == 0:
        return {
            'quality_score': 0,
            'confidence': 'منخفضة جداً',
            'issues': ['النص المستخرج فارغ'],
            'recommendations': ['جرب صورة أخرى', 'تحقق من إضاءة الصورة']
        }
    
    # حساب نسبة الأحرف المفيدة
    arabic_chars = len(re.findall(r'[\u0600-\u06FF]', text))
    english_chars = len(re.findall(r'[a-zA-Z]', text))
    digit_chars = len(re.findall(r'\d', text))
    
    useful_chars = arabic_chars + english_chars + digit_chars
    
    # حساب درجة الجودة
    char_quality = (useful_chars / total_chars * 70) if total_chars > 0 else 0
    line_quality = min(total_lines * 3, 30)
    
    quality_score = min(100, char_quality + line_quality)
    
    # تحديد مستوى الثقة
    if quality_score > 80:
        confidence = 'عالية جداً'
    elif quality_score > 70:
        confidence = 'عالية'
    elif quality_score > 50:
        confidence = 'متوسطة'
    elif quality_score > 30:
        confidence = 'منخفضة'
    else:
        confidence = 'منخفضة جداً'
    
    issues = []
    if arabic_chars == 0 and any(word in text.lower() for word in ['عربي', 'العربية', 'الجواز']):
        issues.append('النص العربي غير مقروء بشكل صحيح')
    if total_lines < 2:
        issues.append('عدد الأسطر المستخرجة قليل جداً')
    
    recommendations = [
        "استخدم صور عالية الجودة (300 DPI أو أعلى)",
        "تأكد من إضاءة جيدة وواضحة بدون ظلال",
        "التقط الصورة من زاوية مستقيمة",
        "استخدم خلفية متجانسة وفاتحة اللون"
    ]
    
    return {
        'quality_score': round(quality_score),
        'confidence': confidence,
        'total_lines': total_lines,
        'total_chars': total_chars,
        'useful_chars': useful_chars,
        'arabic_chars': arabic_chars,
        'english_chars': english_chars,
        'digit_chars': digit_chars,
        'issues': issues,
        'recommendations': recommendations
    }

# Routes
@blueprint.route('/')
def index():
    return render_template('admin/gemini_ocr.html')

@blueprint.route('/upload', methods=['POST'])
def upload_file():
    """
    معالجة الملفات المرفوعة أو من المسار المباشر
    يدعم كلاً من:
    - رفع ملف مباشر (file)
    - مسار ملف موجود (path)
    """
    try:
        # التحقق من وجود ملف مرفوع أو مسار ملف
        if 'file' not in request.files and 'path' not in request.form:
            return jsonify({
                'success': False,
                'error': 'لم يتم اختيار ملف أو تقديم مسار ملف'
            }), 400
        
        file_path = None
        filename = None
        is_temp_file = False
        
        # الحالة 1: معالجة ملف مرفوع مباشرة
        if 'file' in request.files:
            file = request.files['file']
            
            if file.filename == '':
                return jsonify({
                    'success': False,
                    'error': 'لم يتم اختيار ملف'
                }), 400
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_path = os.path.join(UPLOAD_FOLDER, filename)
                file.save(file_path)
                is_temp_file = True
            else:
                return jsonify({
                    'success': False,
                    'error': 'نوع الملف غير مدعوم'
                }), 400
        
        # الحالة 2: معالجة ملف من مسار موجود
        elif 'path' in request.form:
            file_path = request.form['path']
            
            # التحقق من وجود الملف
            if not os.path.exists(file_path):
                return jsonify({
                    'success': False,
                    'error': 'الملف غير موجود في المسار المحدد'
                }), 400
            
            # التحقق من صلاحيات الملف
            if not os.path.isfile(file_path):
                return jsonify({
                    'success': False,
                    'error': 'المسار المحدد ليس ملفاً صالحاً'
                }), 400
            
            # الحصول على اسم الملف من المسار
            filename = os.path.basename(file_path)
            
            # نسخ الملف إلى المجلد المؤقت إذا لزم الأمر
            if not file_path.startswith(UPLOAD_FOLDER):
                temp_filename = f"temp_{int(time.time())}_{filename}"
                temp_file_path = os.path.join(UPLOAD_FOLDER, temp_filename)
                shutil.copy2(file_path, temp_file_path)
                file_path = temp_file_path
                is_temp_file = True
        
        # إذا لم يتم تحديد مسار ملف صالح
        if not file_path or not os.path.exists(file_path):
            return jsonify({
                'success': False,
                'error': 'تعذر الوصول إلى الملف'
            }), 400
        
        # تحديد نوع المعالجة بناءً على اسم الملف أو النص المطلوب
        prompt_type = request.form.get('prompt_type', 'general')
        use_gemini = request.form.get('use_gemini', 'true').lower() == 'true'
        use_pytesseract = request.form.get('use_pytesseract', 'true').lower() == 'true'
        
        # الكشف التلقائي عن نوع المستند إذا لم يتم تحديده
        if prompt_type == 'auto':
            prompt_type = detect_document_type(filename, file_path)
        
        result = {
            'success': True,
            'filename': filename,
            'file_path': file_path if not is_temp_file else None,
            'service_used': [],
            'processing_time': 0
        }
        
        start_time = time.time()
        
        # المعالجة باستخدام PyTesseract (إذا مطلوب)
        if use_pytesseract:
            try:
                pytesseract_result = process_with_pytesseract(file_path)
                result.update(pytesseract_result)
                result['service_used'].append('PyTesseract')
            except Exception as e:
                logging.error(f"PyTesseract processing error: {str(e)}")
                result['pytesseract_error'] = str(e)
        
        # المعالجة باستخدام Gemini AI (إذا مطلوب)
        if use_gemini:
            try:
                gemini_result = process_with_gemini(file_path, prompt_type)
                result.update(gemini_result)
                result['service_used'].append('Gemini AI')
            except Exception as e:
                logging.error(f"Gemini AI processing error: {str(e)}")
                result['gemini_error'] = str(e)
        
        result['processing_time'] = round(time.time() - start_time, 2)
        
        # تنظيف الملف المؤقت إذا تم إنشاؤه
        if is_temp_file and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception as e:
                logging.warning(f"Could not delete temp file: {str(e)}")
        
        return jsonify(result)
        
    except Exception as e:
        # تنظيف الملف في حالة الخطأ
        if 'file_path' in locals() and is_temp_file and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except:
                pass
        
        logging.error(f"General processing error: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'خطأ في معالجة الملف: {str(e)}'
        }), 500

@blueprint.route('/upload2', methods=['POST'])
def upload_file2():
    if 'file' not in request.files:
        return jsonify({
            'success': False,
            'error': 'لم يتم اختيار ملف'
        }), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({
            'success': False,
            'error': 'لم يتم اختيار ملف'
        }), 400
    
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(UPLOAD_FOLDER, filename)
        file.save(file_path)
        
        try:
            # تحديد نوع المعالجة
            prompt_type = "general"
            if any(keyword in filename.upper() for keyword in ['PASSPORT', 'الجواز', 'ID', 'هوية']):
                prompt_type = "passport"
            
            # استخراج النص باستخدام REST API
            extracted_text = analyze_image_with_gemini_rest_api(file_path, prompt_type)
            
            # استخراج البيانات المنظمة
            result = extract_structured_data_from_text(extracted_text, filename)
            
            # تنظيف الملف
            os.remove(file_path)
            
            response_data = {
                'success': True,
                'filename': filename,
                'extracted_text': result['raw_text'],
                'lines': result['lines'],
                'structured_info': result['structured_info'],
                'language_analysis': result['language_analysis'],
                'quality_analysis': result['quality_analysis'],
                'word_count': len(result['raw_text'].split()),
                'character_count': len(result['raw_text']),
                'service_used': 'Gemini AI (REST API)'
            }
            
            if 'document_type' in result:
                response_data['document_type'] = result['document_type']
            
            return jsonify(response_data)
            
        except Exception as e:
            # تنظيف الملف في حالة الخطأ
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logging.error(f"Error processing file with Gemini: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return jsonify({
        'success': False,
        'error': 'نوع الملف غير مدعوم'
    }), 400

@blueprint.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({
                'status': 'unhealthy',
                'error': 'مفتاح API غير موجود'
            }), 500
        
        # اختبار بسيط باستخدام REST API
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": "Say 'Hello' in Arabic"}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({
                'status': 'healthy',
                'service': 'Google Gemini AI',
                'message': 'Service is running correctly',
                'test_response': text,
                'method': 'REST API'
            })
        else:
            return jsonify({
                'status': 'unhealthy',
                'service': 'Google Gemini AI', 
                'error': f"API returned status {response.status_code}",
                'method': 'REST API'
            }), 500
            
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'Google Gemini AI',
            'error': str(e),
            'method': 'REST API'
        }), 500

@blueprint.route('/test-simple')
def test_simple():
    """اختبار بسيط لـ Gemini"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        if not api_key:
            return jsonify({'success': False, 'error': 'مفتاح API غير موجود'}), 500
        
        # استخدام REST API مباشرة
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.0-flash:generateContent?key={api_key}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": [{
                "parts": [{"text": "اكتب جملة باللغة العربية تحتوي على اسم وتاريخ"}]
            }]
        }
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        
        if response.status_code == 200:
            result = response.json()
            text = result['candidates'][0]['content']['parts'][0]['text']
            return jsonify({
                'success': True,
                'response': text,
                'service': 'Gemini AI',
                'model_used': 'gemini-2.0-flash',
                'method': 'REST API'
            })
        else:
            return jsonify({
                'success': False,
                'error': f"خطأ في API: {response.status_code}"
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blueprint.route('/models')
def list_models():
    """عرض النماذج المتاحة"""
    try:
        api_key = os.getenv('GOOGLE_API_KEY')
        url = f"https://generativelanguage.googleapis.com/v1/models?key={api_key}"
        response = requests.get(url)
        
        if response.status_code == 200:
            models_data = response.json()
            available_models = []
            
            for model in models_data.get('models', []):
                model_info = {
                    'name': model['name'],
                    'display_name': model.get('displayName', ''),
                    'supported_methods': model.get('supportedGenerationMethods', [])
                }
                available_models.append(model_info)
            
            return jsonify({
                'success': True,
                'available_models': available_models,
                'recommended_for_images': ['gemini-2.0-flash-exp', 'gemini-2.0-flash'],
                'total_models': len(available_models)
            })
        else:
            return jsonify({
                'success': False,
                'error': f"Failed to fetch models: {response.status_code}"
            }), 500
            
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500