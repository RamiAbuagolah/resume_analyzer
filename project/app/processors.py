import re
from datetime import datetime
from dateutil import parser
import os
from werkzeug.utils import secure_filename
from .extractors import extract_text_from_pdf, extract_text_from_docx, extract_text_from_image,  calculate_years_of_experience


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

def process_file(file_path):
    try:
        if file_path.lower().endswith('.pdf'):
            text = extract_text_from_pdf(file_path)
        elif file_path.lower().endswith('.docx'):
            text = extract_text_from_docx(file_path)
        elif file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            text = extract_text_from_image(file_path)
        else:
            return None, "Unsupported file format"

        years_of_experience = calculate_years_of_experience(text)
        education, job_title = extract_education_and_job_title(text)
        score = calculate_score(years_of_experience, education, job_title)
        
        data = {
            "resume_str": text,
            "years_of_experience": years_of_experience,
            "education": education,
            "job_title": job_title,
            "score": score
        }
        return data, None
    except Exception as e:
        return None, str(e)