import os  # Make sure this import is included
from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from .models import Resume
from .processors import process_file
from . import db
from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine
from sklearn.feature_extraction.text import TfidfVectorizer

bp = Blueprint('main', __name__)

def get_session():
    engine = create_engine(current_app.config['SQLALCHEMY_DATABASE_URI'])
    Session = sessionmaker(bind=engine)
    return Session()

def get_unique_filename(session, filename):
    base, extension = os.path.splitext(filename)
    counter = 1
    new_filename = filename

    while session.query(Resume).filter_by(filename=new_filename).first():
        new_filename = f"{base}({counter}){extension}"
        counter += 1

    return new_filename

@bp.route('/upload-cv', methods=['POST'])
def upload_cv():
    session = get_session()
    
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        filename = get_unique_filename(session, filename)

        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        data, error = process_file(file_path)
        if error:
            return jsonify({"error": error}), 500
        
        resume = Resume(
            filename=filename,
            resume_str=data['resume_str'],
            years_of_experience=data['years_of_experience'],
            education=data['education'],
            job_title=data['job_title'],
            score=data['score']
        )
        session.add(resume)
        session.commit()
        
        return jsonify(data), 200

@bp.route('/upload-cvs', methods=['POST'])
def upload_cvs():
    session = get_session()
    
    if 'files' not in request.files:
        return jsonify({"error": "No file part"}), 400

    files = request.files.getlist('files')
    if len(files) == 0:
        return jsonify({"error": "No selected files"}), 400

    results = []
    for file in files:
        if file:
            filename = secure_filename(file.filename)
            filename = get_unique_filename(session, filename)

            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
            file.save(file_path)
            
            data, error = process_file(file_path)
            if error:
                results.append({"filename": filename, "error": error})
            else:
                resume = Resume(
                    filename=filename,
                    resume_str=data['resume_str'],
                    years_of_experience=data['years_of_experience'],
                    education=data['education'],
                    job_title=data['job_title'],
                    score=data['score']
                )
                session.add(resume)
                session.commit()
                results.append({"filename": filename, "data": data})
    
    return jsonify(results), 200

@bp.route('/search-resumes', methods=['GET'])
def search_resumes():
    session = get_session()
    
    # Get parameters from the request
    query_text = request.args.get('text', '')
    min_years_of_experience = request.args.get('years_of_experience', type=int, default=0)
    education = request.args.get('education', '')
    job_title = request.args.get('job_title', '')
    limit = request.args.get('limit', type=int, default=5)  # Default limit to 5 records
    
    # Process multiple values in the text parameter separated by #
    query_terms = query_text.split('#')
    
    # Filter resumes based on years of experience
    resumes = session.query(Resume).filter(Resume.years_of_experience >= min_years_of_experience)
    
    # Filter based on education if provided
    if education:
        resumes = resumes.filter(Resume.education.ilike(f"%{education}%"))
    
    # Filter based on job title if provided
    if job_title:
        resumes = resumes.filter(Resume.job_title.ilike(f"%{job_title}%"))
    
    resumes = resumes.all()
    
    # Extract resume texts
    resume_texts = [resume.resume_str for resume in resumes if resume.resume_str]
    
    if resume_texts and query_terms:
        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform(resume_texts)
            # Initialize scores to zero
            scores = [0] * len(resumes)
            
            # Calculate scores for each query term
            for term in query_terms:
                query_vec = vectorizer.transform([term])
                term_scores = (tfidf_matrix * query_vec.T).toarray().ravel()
                scores = [sum(x) for x in zip(scores, term_scores)]
            
            # Assign scores to resumes
            for resume, score in zip(resumes, scores):
                resume.text_score = score
            
            # Sort resumes based on text scores
            resumes = sorted(resumes, key=lambda r: r.text_score, reverse=True)
        except ValueError as e:
            print(f"Error in vectorizing texts: {e}")
            # Handle the error or set default behavior
            for resume in resumes:
                resume.text_score = 0
            resumes = sorted(resumes, key=lambda r: r.years_of_experience, reverse=True)
    else:
        # If no valid resume texts or query terms, sort based on years of experience
        for resume in resumes:
            resume.text_score = 0
        resumes = sorted(resumes, key=lambda r: r.years_of_experience, reverse=True)
    
    # Limit the number of results
    resumes = resumes[:limit]

    results = [
        {
            "filename": resume.filename,
            "resume_str": resume.resume_str,
            "years_of_experience": resume.years_of_experience,
            "education": resume.education,
            "job_title": resume.job_title,
            "score": resume.text_score
        } for resume in resumes
    ]

    return jsonify(results), 200