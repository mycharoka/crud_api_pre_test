from flask import Flask, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from werkzeug.security import generate_password_hash, check_password_hash
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("APP_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)

curr = conn.cursor()

try:
  query = "SELECT * FROM users WHERE username = %s"
  values = ['admin']
  curr.execute(query, values)
  query_result = curr.fetchall()
  print('ress >> ', len(query_result))

  if len(query_result) == 0:
    admin_email = os.getenv("ADMIN_EMAIL")
    admin_password = os.getenv("ADMIN_PASSWORD")
    hash_password = generate_password_hash(admin_password)

    query = "INSERT INTO users(email, username, password, role) VALUES (%s, %s, %s, %s)"
    values = [admin_email, 'admin', hash_password, 'admin']
    curr.execute(query, values)
    conn.commit()

    # results = curr.rowcount()
    print("ADMINISTRATOR CREATED!")
    
except(Exception, psycopg2.Error) as error:
  print("Failed to initiate admin user ", error)
finally:
  if conn:
    curr.close()
    conn.close()
    print("Connection to user table closed!")

# if __name__ == "__main__":
#     app.run(debug=True)