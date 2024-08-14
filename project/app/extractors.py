import pdfplumber
from docx import Document
import easyocr
import re
from datetime import datetime
from dateutil import parser
from dateutil.relativedelta import relativedelta
import spacy

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

def extract_text_from_pdf(pdf_path):
    text = ""
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() + "\n"
    return text

def extract_text_from_docx(docx_path):
    doc = Document(docx_path)
    text = "\n".join([para.text for para in doc.paragraphs])
    return text

def extract_text_from_image(image_path):
    reader = easyocr.Reader(['en'])
    result = reader.readtext(image_path, detail=0)
    text = " ".join(result)
    return text

def calculate_years_of_experience(text):
    patterns = [
        r'(\d+)\s+years?\s+of\s+experience',
        r'(\d{4})\s*-\s*(\d{4})',
        r'(\d{4})\s*to\s*(\d{4})',
        r'(\d+)\s*years?\s*(\d+)?\s*months?',
        r'(\d+)\s*months?',
        r'(\w+\s\d{4})\s*-\s*(\w+\s\d{4})',
        r'(\d{1,2}\s\w+\s\d{4})\s*-\s*(\d{1,2}\s\w+\s\d{4})',
        r'(\w+\s\d{4})\s*to\s*(\w+\s\d{4})',
        r'(\d{1,2}\s\w+\s\d{4})\s*to\s*(\d{1,2}\s\w+\s\d{4})',
        r'(\d{4})\s*-\s*Present',
        r'(\d{4})\s*to\s*Present',
        r'(\w+\s\d{4})\s*-\s*Present',
        r'(\d{1,2}\s\w+\s\d{4})\s*-\s*Present',
        r'(\d{1,2}/\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})\s*to\s*(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{1,2}/\d{1,2}/\d{4})\s*-\s*Present',
        r'(\d{1,2}/\d{1,2}/\d{4})\s*to\s*Present',
        r'(\d{1,2}/\d{4})\s*-\s*(\d{1,2}/\d{4})',
        r'(\d{1,2}/\d{4})\s*to\s*(\d{1,2}/\d{4})',
    ]
    
    dates = []
    
    # Extract dates using regex patterns
    for pattern in patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            if isinstance(match, tuple):
                dates.append(" - ".join(match))
            else:
                dates.append(match)
    
    total_duration = relativedelta()
    current_date = datetime.now()
    periods = []

    for date in dates:
        try:
            if 'to' in date or '-' in date or '–' in date:
                start, end = re.split(r'\s*[-–]\s*|\sto\s*', date)
                start_date = parser.parse(start, fuzzy=True)
                if end.lower() in ['present', 'now']:
                    end_date = current_date
                else:
                    end_date = parser.parse(end, fuzzy=True)
            else:
                start_date = parser.parse(date, fuzzy=True)
                end_date = current_date
            periods.append((start_date, end_date))
        except Exception as e:
            print(f"Error parsing date: {date}, {e}")

    # Sort and merge overlapping periods
    periods.sort()
    merged_periods = []
    if periods:
        current_start, current_end = periods[0]

        for start, end in periods[1:]:
            if start <= current_end:
                current_end = max(current_end, end)
            else:
                merged_periods.append((current_start, current_end))
                current_start, current_end = start, end
        merged_periods.append((current_start, current_end))

    total_months = sum((end.year - start.year) * 12 + end.month - start.month for start, end in merged_periods)
    total_years = total_months // 12
    remaining_months = total_months % 12

    return round(total_years + remaining_months / 12, 1)

def extract_education_and_job_title(text):
    education_levels = {
        'bachelor': 'b', 'undergraduate': 'b', 'bsc': 'b', 'ba': 'b',
        'master': 'm', 'graduate': 'm', 'msc': 'm', 'ma': 'm',
        'phd': 'p', 'doctorate': 'p'
    }
    
    job_titles = {
        'manager': 'm', 'mngr': 'm', 'mgr': 'm',
        'leader': 'l', 'ldr': 'l',
        'senior': 's', 'sr': 's',
        'director': 'd', 'dir': 'd',
        'chief': 'c', 'officer': 'c', 'head': 'h',
        'supervisor': 'spv', 'sup': 'spv'
    }
    
    education = ""
    job_title = ""
    
    for level in education_levels:
        if re.search(level, text, re.IGNORECASE):
            education = education_levels[level]
            break
    
    for title in job_titles:
        if re.search(title, text, re.IGNORECASE):
            job_title = job_titles[title]
            break
    
    return education, job_title

def calculate_score(years_of_experience, education, job_title):
    experience_score = 0
    education_score = 0
    job_title_score = 0

    # Calculate experience score
    if years_of_experience > 7:
        experience_score = 100
    elif 3 <= years_of_experience <= 7:
        experience_score = 65
    elif 1 <= years_of_experience < 3:
        experience_score = 25

    # Calculate education score
    if education == 'p':
        education_score = 100
    elif education == 'm':
        education_score = 65
    elif education == 'b':
        education_score = 25

    # Calculate job title score
    if job_title in ['m', 'd', 'c']:
        job_title_score = 100
    elif job_title == 'l':
        job_title_score = 65
    elif job_title in ['s', 'spv']:
        job_title_score = 25

    # Calculate total score
    total_score = (experience_score * 0.4) + (education_score * 0.3) + (job_title_score * 0.3)
    return total_score