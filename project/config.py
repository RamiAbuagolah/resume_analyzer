import os

class Config:
    UPLOAD_FOLDER = 'uploads'
    SQLALCHEMY_DATABASE_URI = "mssql+pyodbc://localhost\\MSSQLSERVER01/AI?driver=ODBC+Driver+17+for+SQL+Server&trusted_connection=yes"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
