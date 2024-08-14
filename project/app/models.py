from . import db

class Resume(db.Model):
    __tablename__ = 'resumes'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    filename = db.Column(db.String, unique=True, nullable=False)
    resume_str = db.Column(db.Text, nullable=False)
    years_of_experience = db.Column(db.Integer, nullable=False)
    education = db.Column(db.String, nullable=False)
    job_title = db.Column(db.String, nullable=False)
    score = db.Column(db.Integer, nullable=False)
