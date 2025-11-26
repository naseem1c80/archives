from flask import Blueprint, render_template, request, jsonify, current_app
import boto3
from botocore.exceptions import ClientError, BotoCoreError
import os
from werkzeug.utils import secure_filename
from dotenv import load_dotenv
import logging
import re
from datetime import datetime

# Load environment variables
load_dotenv()

# Create blueprint
blueprint = Blueprint('textract', __name__, url_prefix='/textract', template_folder='templates')

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf', 'tiff', 'tif'}

# Create upload folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Initialize Textract client
def get_textract_client():
    return boto3.client(
        'textract',
        aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
        aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
        region_name=os.getenv('AWS_REGION', 'us-east-1')
    )

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def contains_arabic(text):
    """Check if text contains Arabic characters"""
    if not text:
        return False
    arabic_pattern = re.compile('[\u0600-\u06FF\u0750-\u077F\u08A0-\u08FF]+')
    return bool(arabic_pattern.search(text))

def detect_languages(text_blocks):
    """Detect languages in the text"""
    languages = set()
    arabic_count = 0
    english_count = 0
    total_lines = len(text_blocks) if text_blocks else 0
    
    for text in text_blocks:
        if contains_arabic(text):
            languages.add('Arabic')
            arabic_count += 1
        elif re.match(r'^[a-zA-Z0-9\s\W]+$', text) and text.strip():
            languages.add('English')
            english_count += 1
        elif text.strip():
            languages.add('Mixed/Other')
    
    # تحويل set إلى list للتأكد من أننا نتعامل مع مصفوفة
    detected_languages = list(languages) if languages else ['Unknown']
    
    return {
        'detected_languages': detected_languages,
        'arabic_lines_count': arabic_count,
        'english_lines_count': english_count,
        'total_lines': total_lines,
        'arabic_ratio': arabic_count / total_lines if total_lines > 0 else 0,
        'english_ratio': english_count / total_lines if total_lines > 0 else 0
    }

def extract_forms_data(response):
    """Extract form data (key-value pairs)"""
    forms = {}
    key_map = {}
    value_map = {}
    block_map = {}
    
    # Create block map for easy access
    for block in response.get('Blocks', []):
        block_id = block['Id']
        block_map[block_id] = block
        
        if block['BlockType'] == "KEY_VALUE_SET":
            if 'KEY' in block['EntityTypes']:
                key_map[block_id] = block
            else:
                value_map[block_id] = block
    
    # Link keys with values
    for block_id, key_block in key_map.items():
        value_block = find_value_block(key_block, value_map, block_map)
        if value_block:
            key_text = get_text_from_block(key_block, block_map)
            value_text = get_text_from_block(value_block, block_map)
            
            # Clean and classify the form field
            clean_key = clean_arabic_text(key_text)
            clean_value = clean_arabic_text(value_text)
            
            forms[clean_key] = {
                'value': clean_value,
                'is_arabic': contains_arabic(clean_value),
                'confidence': key_block.get('Confidence', 0)
            }
    
    return forms

def find_value_block(key_block, value_map, block_map):
    """Find the value block associated with a key block"""
    for relationship in key_block.get('Relationships', []):
        if relationship['Type'] == 'VALUE':
            for value_id in relationship['Ids']:
                if value_id in value_map:
                    return value_map[value_id]
    return None

def get_text_from_block(block, block_map):
    """Extract text from a block"""
    text = ''
    if 'Relationships' in block:
        for relationship in block['Relationships']:
            if relationship['Type'] == 'CHILD':
                for child_id in relationship['Ids']:
                    child = block_map[child_id]
                    if child['BlockType'] == 'WORD':
                        text += child['Text'] + ' '
    return text.strip()

def extract_tables_data(response):
    """Extract table data from Textract response"""
    tables = []
    
    for block in response.get('Blocks', []):
        if block['BlockType'] == 'TABLE':
            table_data = extract_table_structure(block, response['Blocks'])
            if table_data:
                tables.append(table_data)
    
    return tables

def extract_table_structure(table_block, all_blocks):
    """Extract structure from a single table"""
    table_map = {block['Id']: block for block in all_blocks}
    cells = []
    
    # Find all cells in the table
    for relationship in table_block.get('Relationships', []):
        if relationship['Type'] == 'CHILD':
            for cell_id in relationship['Ids']:
                cell_block = table_map.get(cell_id)
                if cell_block and cell_block['BlockType'] == 'CELL':
                    cell_text = get_text_from_block(cell_block, table_map)
                    cells.append({
                        'row_index': cell_block.get('RowIndex', 0),
                        'column_index': cell_block.get('ColumnIndex', 0),
                        'text': clean_arabic_text(cell_text),
                        'is_arabic': contains_arabic(cell_text)
                    })
    
    # Organize cells by rows
    rows = {}
    for cell in cells:
        row_index = cell['row_index']
        if row_index not in rows:
            rows[row_index] = []
        rows[row_index].append(cell)
    
    # Sort and structure the table
    structured_table = []
    for row_index in sorted(rows.keys()):
        row_cells = sorted(rows[row_index], key=lambda x: x['column_index'])
        structured_row = [cell['text'] for cell in row_cells]
        structured_table.append(structured_row)
    
    return structured_table

def clean_arabic_text(text):
    """Clean and normalize Arabic text"""
    if not text:
        return text
    
    # Remove extra spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Normalize Arabic characters (optional - can be expanded)
    replacements = {
        'ي': 'ی',  # Normalize Ya
        'ك': 'ک',  # Normalize Kaf
    }
    
    for old, new in replacements.items():
        text = text.replace(old, new)
    
    return text

def extract_text_from_response(response):
    """Extract and format text from Textract response with Arabic support"""
    text_blocks = []
    arabic_text_blocks = []
    english_text_blocks = []
    
    # Extract all text lines
    for item in response.get('Blocks', []):
        if item['BlockType'] == 'LINE':
            text = item['Text']
            text_blocks.append(text)
            
            # Classify text as Arabic or English
            if contains_arabic(text):
                arabic_text_blocks.append(text)
            else:
                english_text_blocks.append(text)
    
    # Extract form data (key-value pairs)
    forms = extract_forms_data(response)
    
    # Extract table data
    tables = extract_tables_data(response)
    
    full_text = '\n'.join(text_blocks) if text_blocks else ""
    
    # الحصول على تحليل اللغة مع معالجة الأخطاء
    lang_analysis = detect_languages(text_blocks)
    
    return {
        'raw_text': full_text,
        'lines': text_blocks,
        'arabic_text': arabic_text_blocks,
        'english_text': english_text_blocks,
        'forms': forms,
        'tables': tables,
        'language_analysis': lang_analysis
    }

def validate_response_data(response_data):
    """Validate and clean response data before sending to client"""
    
    # التأكد من أن language_analysis يحتوي على مصفوفة
    if 'language_analysis' in response_data:
        lang_analysis = response_data['language_analysis']
        
        if 'detected_languages' in lang_analysis:
            if not isinstance(lang_analysis['detected_languages'], list):
                lang_analysis['detected_languages'] = ['Unknown']
        
        # تعيين قيم افتراضية للحقول المطلوبة
        lang_analysis.setdefault('arabic_lines_count', 0)
        lang_analysis.setdefault('english_lines_count', 0)
        lang_analysis.setdefault('total_lines', 0)
        lang_analysis.setdefault('detected_languages', ['Unknown'])
        lang_analysis.setdefault('arabic_ratio', 0)
        lang_analysis.setdefault('english_ratio', 0)
    
    # التأكد من أن الحقول الأخرى موجودة
    response_data.setdefault('arabic_text', [])
    response_data.setdefault('english_text', [])
    response_data.setdefault('lines', [])
    response_data.setdefault('forms', {})
    response_data.setdefault('tables', [])
    response_data.setdefault('raw_text', '')
    
    return response_data

def process_passport_data(extracted_data):
    """Process passport data with Arabic text handling"""
    passport_info = {
        'personal_info': {},
        'document_info': {},
        'raw_analysis': extracted_data
    }
    
    lines = extracted_data['lines']
    
    # Extract key passport fields with Arabic support
    for i, line in enumerate(lines):
        line_clean = clean_arabic_text(line)
        
        # Passport Number
        if any(keyword in line.upper() for keyword in ['PASSPORT', 'الجواز']):
            for j in range(i+1, min(i+3, len(lines))):
                if re.search(r'\d{6,9}', lines[j]):
                    passport_info['document_info']['passport_number'] = re.search(r'\d{6,9}', lines[j]).group()
                    break
        
        # Names (handle both Arabic and English)
        elif any(keyword in line.upper() for keyword in ['SURNAME', 'AL-FAKIH', 'اللقب']):
            passport_info['personal_info']['surname'] = extract_name_field(lines, i, 'AL-FAKIH')
        
        elif any(keyword in line.upper() for keyword in ['GIVEN', 'ASEEL', 'الأسماء']):
            passport_info['personal_info']['given_names'] = extract_name_field(lines, i, 'ASEEL')
        
        # Dates
        elif any(keyword in line.upper() for keyword in ['DATE OF BIRTH', 'تاريخ الميلاد']):
            passport_info['personal_info']['date_of_birth'] = extract_date_field(lines, i)
        
        elif any(keyword in line.upper() for keyword in ['DATE OF EXPIRY', 'تاريخ الانتهاء']):
            passport_info['document_info']['expiry_date'] = extract_date_field(lines, i)
    
    return passport_info

def extract_name_field(lines, start_index, default_name):
    """Extract name field with Arabic text handling"""
    for i in range(start_index, min(start_index + 5, len(lines))):
        line = lines[i].strip()
        if line and not any(keyword in line.upper() for keyword in ['SURNAME', 'GIVEN', 'DATE', 'PLACE']):
            # Clean the name
            clean_name = clean_arabic_text(line)
            # Remove common noise words
            noise_words = ['the', 'The', 'jus', 'Just', 'Licell', 'bearer']
            for word in noise_words:
                clean_name = re.sub(r'\b' + word + r'\b', '', clean_name, flags=re.IGNORECASE)
            clean_name = re.sub(r'\s+', ' ', clean_name).strip()
            return clean_name if clean_name else default_name
    return default_name

def extract_date_field(lines, start_index):
    """Extract date field"""
    for i in range(start_index, min(start_index + 5, len(lines))):
        line = lines[i].strip()
        # Look for date patterns
        date_patterns = [
            r'\d{2}/\d{2}/\d{4}',
            r'\d{4}/\d{2}/\d{2}',
            r'\d{2}-\d{2}-\d{4}',
            r'\d{4}-\d{2}-\d{2}'
        ]
        for pattern in date_patterns:
            match = re.search(pattern, line)
            if match:
                return match.group()
    return None

# Text extraction functions
def extract_text_from_image(image_path):
    """Extract text from image using Textract"""
    try:
        textract_client = get_textract_client()
        
        with open(image_path, 'rb') as document:
            image_bytes = document.read()
        
        response = textract_client.detect_document_text(
            Document={'Bytes': image_bytes}
        )
        
        return extract_text_from_response(response)
    
    except (ClientError, BotoCoreError) as e:
        logging.error(f"AWS Textract error: {str(e)}")
        raise Exception(f"AWS Service error: {str(e)}")
    except Exception as e:
        logging.error(f"Error processing image: {str(e)}")
        raise

def extract_text_from_pdf(pdf_path):
    """Extract text from PDF using Textract"""
    try:
        textract_client = get_textract_client()
        
        with open(pdf_path, 'rb') as document:
            pdf_bytes = document.read()
        
        response = textract_client.analyze_document(
            Document={'Bytes': pdf_bytes},
            FeatureTypes=['TABLES', 'FORMS']
        )
        
        return extract_text_from_response(response)
    
    except (ClientError, BotoCoreError) as e:
        logging.error(f"AWS Textract error: {str(e)}")
        raise Exception(f"AWS Service error: {str(e)}")
    except Exception as e:
        logging.error(f"Error processing PDF: {str(e)}")
        raise

# Routes
@blueprint.route('/')
def index():
    return render_template('admin/textract.html')

@blueprint.route('/upload', methods=['POST'])
def upload_file():
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
            # Determine file type and process accordingly
            file_extension = filename.rsplit('.', 1)[1].lower()
            
            if file_extension == 'pdf':
                result = extract_text_from_pdf(file_path)
            else:
                result = extract_text_from_image(file_path)
                print(f'{result}')
            
            # Clean up uploaded file
            os.remove(file_path)
            
            # Add passport data processing for images that look like passports
            passport_data = None
            if result['raw_text'] and any(keyword in result['raw_text'].upper() for keyword in ['PASSPORT', 'YEMEN', 'الجواز', 'اليمن']):
                passport_data = process_passport_data(result)
            
            # التحقق من صحة البيانات قبل الإرسال
            result = validate_response_data(result)
            
            response_data = {
                'success': True,
                'filename': filename,
                'extracted_text': result['raw_text'],
                'lines': result['lines'],
                'arabic_text': result['arabic_text'],
                'english_text': result['english_text'],
                'forms': result['forms'],
                'tables': result['tables'],
                'language_analysis': result['language_analysis'],
                'word_count': len(result['raw_text'].split()),
                'character_count': len(result['raw_text'])
            }
            
            if passport_data:
                response_data['passport_data'] = passport_data
            
            return jsonify(response_data)
            
        except Exception as e:
            # Clean up uploaded file in case of error
            if os.path.exists(file_path):
                os.remove(file_path)
            
            logging.error(f"Error processing file: {str(e)}")
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    return jsonify({
        'success': False,
        'error': 'نوع الملف غير مدعوم. الأنواع المسموحة: PNG, JPG, JPEG, PDF, TIFF'
    }), 400

@blueprint.route('/extract-text', methods=['POST'])
def extract_text_api():
    """API endpoint for text extraction"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'لم يتم تقديم ملف'}), 400
        
        file = request.files['file']
        
        if file.filename == '':
            return jsonify({'error': 'لم يتم اختيار ملف'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'نوع الملف غير مسموح'}), 400
        
        # Process file in memory
        file_bytes = file.read()
        
        textract_client = get_textract_client()
        
        if file.filename.lower().endswith('.pdf'):
            response = textract_client.analyze_document(
                Document={'Bytes': file_bytes},
                FeatureTypes=['TABLES', 'FORMS']
            )
        else:
            response = textract_client.detect_document_text(
                Document={'Bytes': file_bytes}
            )
        
        result = extract_text_from_response(response)
        
        # التحقق من صحة البيانات
        result = validate_response_data(result)
        
        return jsonify({
            'success': True,
            'filename': file.filename,
            'extracted_text': result['raw_text'],
            'lines': result['lines'],
            'arabic_text': result['arabic_text'],
            'english_text': result['english_text'],
            'language_analysis': result['language_analysis'],
            'word_count': len(result['raw_text'].split()),
            'character_count': len(result['raw_text'])
        })
        
    except Exception as e:
        logging.error(f"API Error: {str(e)}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@blueprint.route('/arabic-support')
def arabic_support_info():
    """Information about Arabic text extraction support"""
    return jsonify({
        'arabic_support': True,
        'features': [
            'Arabic character detection',
            'Arabic text classification',
            'Bilingual document processing',
            'Arabic text cleaning and normalization',
            'Form field extraction for Arabic documents',
            'Passport and ID card processing'
        ],
        'supported_documents': [
            'Arabic passports',
            'Yemeni national IDs',
            'Arabic invoices',
            'Bilingual documents',
            'Arabic official forms'
        ],
        'notes': [
            'Textract has good support for Arabic text recognition',
            'For best results, use high-quality images (300+ DPI)',
            'Ensure good contrast between text and background',
            'Arabic text mixed with English is supported'
        ]
    })

@blueprint.route('/debug-response')
def debug_response():
    """Endpoint for debugging response structure"""
    sample_response = {
        'language_analysis': {
            'detected_languages': ['Arabic', 'English'],
            'arabic_lines_count': 5,
            'english_lines_count': 3,
            'total_lines': 8,
            'arabic_ratio': 0.625,
            'english_ratio': 0.375
        }
    }
    
    validated = validate_response_data(sample_response)
    return jsonify({
        'sample_response': sample_response,
        'validated_response': validated,
        'is_array': isinstance(validated['language_analysis']['detected_languages'], list)
    })

@blueprint.route('/health')
def health_check():
    """Health check endpoint"""
    try:
        client = get_textract_client()
        client.list_adapters(MaxResults=1)
        return jsonify({
            'status': 'healthy',
            'service': 'AWS Textract',
            'message': 'Service is running correctly'
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'service': 'AWS Textract',
            'error': str(e)
        }), 500