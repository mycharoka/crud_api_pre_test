from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from psycopg2.extras import RealDictCursor
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from flask_migrate import Migrate
from dotenv import load_dotenv
import psycopg2
import os

load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv("APP_KEY")
app.config['JWT_KEY'] = os.getenv("JWT_KEY")
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv("SQLALCHEMY_DATABASE_URI")

jwt = JWTManager(app)
db = SQLAlchemy(app)
migrate = Migrate(app, db)


DB_HOST = os.getenv("DB_HOST")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_PORT = os.getenv("DB_PORT")

conn = psycopg2.connect(dbname=DB_NAME, user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT)


class Employee(db.Model):
  __tablename__ = 'employee'
  id = db.Column(db.Integer, primary_key=True)
  name = db.Column(db.String)
  birthday = db.Column(db.DateTime)
  birth_place = db.Column(db.String)
  nik = db.Column(db.Integer)
  position = db.Column(db.String)
  date_hired = db.Column(db.DateTime)
  created_at = db.Column(db.DateTime)
  
class User(db.Model):
  __tablename__ = 'users'
  id = db.Column(db.Integer, primary_key=True)
  email = db.Column(db.String, nullable=False)
  username = db.Column(db.String, nullable=False)
  password = db.Column(db.String, nullable=False)
  role = db.Column(db.String)



@app.route('/employee')
@jwt_required()
def get_all_employees():
  users = get_jwt_identity()
  
  if users != "admin":
    return not_allowed()
  
  curr = conn.cursor(cursor_factory=RealDictCursor)
  curr.execute("SELECT * FROM employee")
  msg = {'data': curr.fetchall()}
  return msg

@app.route('/employee/<nik>')
@jwt_required()
def get_employee_by_nik(nik):
  users = get_jwt_identity()
  if users != "admin":
    return not_allowed()
  
  curr = conn.cursor(cursor_factory=RealDictCursor)
  # query = 'SELECT row_to_json(row) FROM (SELECT * FROM employee WHERE nik = %s) row'
  query = 'SELECT * FROM employee WHERE nik = %s'
  value = [nik]
  curr.execute(query, value)
  # res = json.dumps(curr.fetchall())
  msg = {'data': curr.fetchall()}
  # return json.loads(res)
  return msg

@app.route('/signup', methods=['POST'])
@jwt_required()
def signup():
  users = get_jwt_identity()
  if users != "admin":
    return not_allowed()

  req = request.json
  
  _email = req['email']
  _name = req['name']
  _role = req['role']
  _password = req['password']

  curr = conn.cursor()

  is_user_exist = "SELECT * FROM users WHERE email = %s AND username = %s AND role = %s"
  values = (_email, _name, _role)
  curr.execute(is_user_exist, values)
  results = curr.fetchall()
  

  if _name.lower() == "admin":
    return user_not_allowed()

  if len(results) == 0:
    
    hash_password = generate_password_hash(_password)
    
    try:
      regist_user = "INSERT INTO users(email, username, password, role) VALUES(%s, %s, %s, %s)"
      
      values = (_email, _name, hash_password, _role)
      

      curr.execute(regist_user, values)
      conn.commit()
      results = curr.rowcount
      

      msg = {
        'status': 200,
        'message': f'{_name} with role {_role} registered!'
      }

      response = jsonify(msg)
      response.status_code = 200

      return response
    

    except(Exception, psycopg2.Error) as error:
      return {
        'status': 500,
        'message': 'Insert to table error: ' + error 
      }
  
  else:
    return user_exist()


@app.route('/login', methods=['POST'])
def login():
  req = request.json
  curr = conn.cursor(cursor_factory=RealDictCursor)
  _email = req['email']
  _password = req['password']

  try:
    query = "SELECT * FROM users WHERE email = %s"
    # query = "SELECT row_to_json(row) FROM (SELECT * FROM users WHERE email = %s) row"
    value = [_email]
    curr.execute(query, value)
    results = curr.fetchone()

    if results == None:
      return not_exist()
    else:
      check_password = check_password_hash(results['password'], _password)
      

      if check_password:
        token = create_access_token(identity=results['role'])
        msg = {
          'status': 200,
          'message': 'Login Success',
          'token': f'Bearer {token}'
        }
        return msg
      else:
        return password_mismatch()
  except(Exception, psycopg2.Error) as error:
    return {
      'statis': 500,
      'message': f'Something must be error {error}'
    }

@app.route('/employee', methods=['POST'])
@jwt_required()
def add_employee():
  users = get_jwt_identity()
  if users != "admin": 
    return not_allowed()

  req = request.json
  curr = conn.cursor()
  
  _name = req['name']
  _birthday = req['birthday']
  _birth_place = req['birth_place']
  _nik = req['nik']
  _position = req['position']
  _date_hired = req['date_hired']

  is_nik_exist = "SELECT nik FROM employee WHERE nik = %s"
  val = [_nik]
  curr.execute(is_nik_exist, val)
  validate_nik = curr.fetchall()
  

  if len(validate_nik) > 0:
    return already_exist()

  try:
    query = "INSERT INTO employee(name, birthday, birth_place, nik, position, date_hired, created_at) VALUES(%s, %s, %s, %s, %s, %s, CURRENT_TIMESTAMP::TIMESTAMP(0))"
    
    values = (_name, _birthday, _birth_place, _nik, _position, _date_hired)
    
    # 
    curr.execute(query, values)
    conn.commit()
    results = curr.rowcount
    

    return {
      'status': 200,
      'message': 'Added'
    }
  
  except(Exception, psycopg2.Error) as error:
    return {
      'status': 500,
      'message': 'Insert to Employee table error ' + error
    }

@app.route('/employee/<nik>', methods=['DELETE'])
@jwt_required()
def del_employee(nik):
  users = get_jwt_identity()
  if users != "admin":
    return not_allowed()

  
  curr = conn.cursor()
  query = "SELECT * FROM employee WHERE nik = %s"
  value = [nik]
  curr.execute(query, value)
  validate_nik = curr.fetchall()
  

  if len(validate_nik) == 0:
    return not_exist()
  
  else:
    try:
      query = "DELETE FROM employee WHERE nik = %s"
      value = [nik]
      curr.execute(query, value)
      conn.commit()
      results = curr.rowcount
      

      return {
        'status': 200,
        'message': f'Employee with NIK: {nik} has been deleted!'
      }

    except(Exception, psycopg2.Error) as error:
      return {
        'status': 500,
        'message': error
      }
    

@app.route('/employee/<nik>', methods=['PUT'])
@jwt_required()
def edit_employee(nik):
  users = get_jwt_identity()
  if users != "admin":
    return not_allowed()

  req = request.json
  curr = conn.cursor()
  query = "SELECT * FROM employee WHERE nik = %s"
  value = [nik]
  curr.execute(query, value)
  validate_nik = curr.fetchall()

  if len(validate_nik) == 0:
    return not_exist()
  
  else:
    try:
      _name = req['name']
      _birthday = req['birthday']
      _birth_place = req['birth_place']
      _position = req['position']

      query = "UPDATE employee SET name = %s, birthday = %s, birth_place = %s, position = %s WHERE nik = %s"
      values = [_name, _birthday, _birth_place, _position, nik]
      curr.execute(query, values)
      conn.commit()
      results = curr.rowcount
      

      return {
        'status': 200,
        'message': f'Employee with NIK: {nik} has been updated!'
      }

    except(Exception, psycopg2.Error) as error:
      return {
        'status': 500,
        'message': error
      }



@app.errorhandler(400)
def user_exist(error=None):
  msg = {
    'status': 400,
    'message': 'User Already Exist!'
  }

  res = jsonify(msg)
  res.status_code = 400

  return res

@app.errorhandler(500)
def user_not_allowed(error=None):
  msg = {
    'status': 500,
    'message': 'Cannot Register Admin User!'
  }

  res = jsonify(msg)
  res.status_code = 500

  return res

@app.errorhandler(400)
def already_exist(error=None):
  msg = {
    'status': 400,
    'message': 'Data Already Exist'
  }
  res = jsonify(msg)
  res.status_code = 400

  return res

@app.errorhandler(400)
def not_exist(error=None):
  msg = {
    'status': 400,
    'message': 'Data Not Exist'
  }

  res = jsonify(msg)
  res.status_code = 400

  return res

@app.errorhandler(400)
def password_mismatch(error=None):
  msg ={
    'status': 400,
    'message': 'Password Incorrect'
  }

  res = jsonify(msg)
  res.status_code = 400

  return res

@app.errorhandler(400)
def not_allowed(error=None):
  msg = {
    'status': 400,
    'message': 'Admin Access Only'
  }

  res = jsonify(msg)
  res.status_code = 400

  return res

if __name__ == "__main__":
  app.run(host='localhost', port=3000, debug=True)

