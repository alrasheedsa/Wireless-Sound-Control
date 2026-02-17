# استيراد المكتبات اللازمة
import os
# مكتبة للتعامل مع نظام الملفات (File System)
import cv2
# مكتبة OpenCV لمعالجة الصور والفيديو (Computer Vision)
import jwt
# مكتبة لإنشاء وفك تشفير التوكنات (JSON Web Token)
import datetime
# مكتبة للتعامل مع التواريخ والأوقات
import base64
# مكتبة لتشفير وفك تشفير البيانات بصيغة Base64
import pickle
# مكتبة لتسلسل البيانات (Serialization) وحفظها
import threading
# مكتبة لإنشاء وإدارة الخيوط (Threads)
import queue
# مكتبة لإنشاء قوائم انتظار (Queue) لتخزين البيانات مؤقتًا
from flask import Flask, render_template, request, jsonify, Response, send_from_directory
# مكتبات Flask لإنشاء خادم ويب، معالجة الطلبات، وإرسال الردود
from flask_cors import CORS
# مكتبة لتمكين مشاركة الموارد عبر المصادر (Cross-Origin Resource Sharing)
from flask_socketio import SocketIO, emit
# مكتبة للتفاعل في الوقت الفعلي عبر WebSocket
import mysql
# مكتبة للتعامل مع قواعد بيانات MySQL
from werkzeug.security import generate_password_hash, check_password_hash
# دوال لتشفير كلمات المرور والتحقق منها
from database import get_db_connection, get_mysql_connection
# دوال مخصصة لإنشاء اتصال بقاعدة البيانات
from Gesture_Face_Volume import GestureFaceVolumeController
# فئة مخصصة للتحكم في الصوت باستخدام الإيماءات والتعرف على الوجه


# إنشاء تطبيق Flask
app = Flask(__name__, static_folder='static')
# تحديد مجلد الملفات الثابتة (Static Files)
CORS(app)
# تمكين CORS للسماح بالطلبات من مصادر مختلفة
app.config['SECRET_KEY'] = 'abc123xyz789'
# مفتاح سري لتشفير التوكنات (Secret Key)
app.config['MYSQL_CONFIG'] = {
    'host': 'localhost',
    'user': 'root',
    'password': '',
    'database': 'wireless'
}
# إعدادات قاعدة بيانات MySQL
socketio = SocketIO(app, cors_allowed_origins="*")
# إنشاء كائن SocketIO للتفاعل في الوقت الفعلي

# إنشاء قائمة انتظار لتخزين إطارات الفيديو (Frames)
frame_queue = queue.Queue()
# متغيرات عالمية للتحكم في معالجة الإيماءات
gesture_controller = None
controller_thread = None

# دالة لإنشاء توكن (JWT Token)
def generate_token(user_id):
    # إنشاء حمولة (Payload) تحتوي على معرف المستخدم وتاريخ الانتهاء
    payload = {
        'user_id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
    }
    # تشفير الحمولة باستخدام المفتاح السري
    return jwt.encode(payload, app.config['SECRET_KEY'], algorithm='HS256')

# دالة لفك تشفير التوكن
def decode_token(token):
    try:
        # فك تشفير التوكن باستخدام المفتاح السري
        payload = jwt.decode(token, app.config['SECRET_KEY'], algorithms=['HS256'])
        return payload['user_id']
    except jwt.ExpiredSignatureError:
        # إذا انتهت صلاحية التوكن
        return None
    except jwt.InvalidTokenError:
        # إذا كان التوكن غير صالح
        return None

# مسار لخدمة الملفات الثابتة (Static Files)
@app.route('/<path:filename>')
def serve_static(filename):
    # إرسال الملف من مجلد الملفات الثابتة
    return send_from_directory(app.static_folder, filename)

# المسار الرئيسي لعرض الصفحة الرئيسية
@app.route('/')
def index():
    # عرض ملف index.html
    return render_template('index.html')

# مسار التسجيل (Signup)
@app.route('/api/auth/signup', methods=['POST'])
def signup():
    try:
        # استرجاع بيانات النموذج
        username = request.form.get('username')
        email = request.form.get('email')
        password = request.form.get('password')
        phone_number = request.form.get('phoneNumber')
        face_image = request.files.get('faceImage')

        # التحقق من وجود جميع الحقول
        if not all([username, email, password, phone_number, face_image]):
            return jsonify({'message': 'All fields are required'}), 400

        # التحقق من صحة البيانات باستخدام تعبيرات منتظمة (Regular Expressions)
        import re
        if not re.match(r'^[A-Za-z0-9]+$', username):
            return jsonify({'message': 'Username must contain only English letters and numbers'}), 400
        if not re.match(r'^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$', email):
            return jsonify({'message': 'Invalid email format'}), 400
        if not re.match(r'^[A-Za-z0-9!@#$%^&*]+$', password):
            return jsonify({'message': 'Password has invalid characters'}), 400
        if not re.match(r'^[0-9]+$', phone_number):
            return jsonify({'message': 'Phone number must contain only digits'}), 400

        # تشفير كلمة المرور
        hashed_password = generate_password_hash(password)
        # قراءة بيانات الصورة
        image_data = face_image.read()

        # التحقق من صحة الصورة
        if not image_data:
            return jsonify({'message': 'Invalid or empty image file'}), 400

        # معالجة الصورة باستخدام مكتبة face_recognition
        import face_recognition, pickle
        temp_file = 'temp_image.jpg'
        # حفظ الصورة مؤقتًا
        with open(temp_file, 'wb') as f:
            f.write(image_data)
        # تحميل الصورة
        image = face_recognition.load_image_file(temp_file)
        # استخراج ترميز الوجه (Face Encoding)
        encodings = face_recognition.face_encodings(image)
        # حذف الملف المؤقت
        os.remove(temp_file)

        # التحقق من وجود وجه في الصورة
        if not encodings:
            return jsonify({'message': 'No face detected in the image'}), 400

        # تسلسل ترميز الوجه (Serialization)
        encoding_data = pickle.dumps(encodings[0])

        # طباعة حجم البيانات للتصحيح
        print(f"[Signup] Encoding size: {len(encoding_data)} bytes")
        print(f"[Signup] Image size: {len(image_data)} bytes")

        # الاتصال بقاعدة البيانات
        db = get_mysql_connection()
        cursor = db.cursor()

        try:
            # التحقق من وجود البريد الإلكتروني مسبقًا
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({'message': 'Email already exists'}), 400

            # إدراج بيانات المستخدم
            cursor.execute("""
                INSERT INTO users (username, email, password, phone_number)
                VALUES (%s, %s, %s, %s)
            """, (username, email, hashed_password, phone_number))
            user_id = cursor.lastrowid

            # إدراج ترميز الوجه وبيانات الصورة
            cursor.execute("""
                INSERT INTO face_encodings (user_id, encoding_data, image_data, reference_image_path)
                VALUES (%s, %s, %s, %s)
            """, (user_id, bytearray(encoding_data), bytearray(image_data), f'user_{user_id}_face.jpg'))

            # تأكيد التغييرات
            db.commit()
            print(f"[Signup] Successfully registered user {username} (ID: {user_id})")
        except mysql.connector.Error as err:
            # إلغاء التغييرات في حالة الخطأ
            db.rollback()
            return jsonify({'message': f'Database error: {str(err)}'}), 500
        finally:
            # إغلاق المؤشر والاتصال
            cursor.close()
            db.close()

        return jsonify({'message': 'Signup successful'}), 200

    except Exception as e:
        # معالجة الأخطاء العامة
        print(f"[Signup Error] {str(e)}")
        return jsonify({'message': f'Error: {str(e)}'}), 500

# مسار تسجيل الدخول (Signin)
@app.route('/api/auth/signin', methods=['POST'])
def signin():
    # استرجاع بيانات الطلب
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    # التحقق من وجود الحقول
    if not email or not password:
        return jsonify({'message': 'Email and password are required'}), 400

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # البحث عن المستخدم باستخدام البريد أو اسم المستخدم
        query = "SELECT * FROM users WHERE email = %s OR username = %s"
        cursor.execute(query, (email, email))
        user = cursor.fetchone()

        # التحقق من صحة بيانات تسجيل الدخول
        if not user or not check_password_hash(user['password'], password):
            return jsonify({'message': 'Invalid credentials'}), 401

        # إنشاء توكن للمستخدم
        token = generate_token(user['id'])
        print(f"[Signin] User {user['username']} signed in successfully")
        return jsonify({
            'token': token,
            'user': {
                'id': user['id'],
                'username': user['username'],
                'email': user['email'],
                'role': user['role']
            }
        }), 200
    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500
    finally:
        cursor.close()
        db.close()

# مسار نسيان كلمة المرور (Forgot Password)
@app.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    # استرجاع البريد الإلكتروني
    data = request.get_json()
    email = data.get('email')

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    cursor = db.cursor()
    try:
        # التحقق من وجود البريد
        query = "SELECT id FROM users WHERE email = %s"
        cursor.execute(query, (email,))
        user = cursor.fetchone()

        if not user:
            return jsonify({'message': 'Email not found'}), 404

        # محاكاة إرسال رابط إعادة تعيين كلمة المرور
        return jsonify({'message': 'Password reset link sent to your email'}), 200
    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500
    finally:
        cursor.close()
        db.close()

# مسار إنشاء محاضرة (Create Lecture)
@app.route('/api/lectures', methods=['POST'])
def create_lecture():
    # التحقق من التوكن
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = decode_token(token)
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # استرجاع بيانات الطلب
    data = request.get_json()
    user_name = data.get('userName')
    topic = data.get('topic')
    date = data.get('date')

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    cursor = db.cursor()
    try:
        # إدراج بيانات المحاضرة
        query = """
            INSERT INTO lectures (user_id, name_of_user, topic, date)
            VALUES (%s, %s, %s, %s)
        """
        cursor.execute(query, (user_id, user_name, topic, date))
        lecture_id = cursor.lastrowid
        db.commit()
        print(f"[Create Lecture] Lecture created with ID {lecture_id} by user_id {user_id}")
        return jsonify({'message': 'Lecture created', 'lecture_id': lecture_id}), 200
    except mysql.connector.Error as err:
        db.rollback()
        return jsonify({'message': f'Database error: {str(err)}'}), 500
    finally:
        cursor.close()
        db.close()

# مسار إدارة ملف تعريف المستخدم (User Profile)
@app.route('/api/user/profile', methods=['GET', 'PUT'])
def user_profile():
    # التحقق من التوكن
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = decode_token(token)
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    if request.method == 'GET':
        # استرجاع بيانات المستخدم
        cursor = db.cursor(dictionary=True)
        try:
            query = "SELECT username, email, phone_number FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            user = cursor.fetchone()
            if not user:
                return jsonify({'message': 'User not found'}), 404

            # استرجاع صورة الوجه
            query = "SELECT image_data FROM face_encodings WHERE user_id = %s"
            cursor.execute(query, (user_id,))
            face_data = cursor.fetchone()
            image = None
            if face_data and face_data['image_data']:
                image = f"data:image/jpeg;base64,{base64.b64encode(face_data['image_data']).decode('utf-8')}"
            
            user['image'] = image
            return jsonify(user), 200
        except mysql.connector.Error as err:
            return jsonify({'message': f'Database error: {str(err)}'}), 500
        finally:
            cursor.close()
            db.close()

    elif request.method == 'PUT':
        # تحديث بيانات المستخدم
        cursor = db.cursor()
        try:
            username = request.form.get('username')
            email = request.form.get('email')
            password = request.form.get('password')
            phone_number = request.form.get('phoneNumber')
            face_image = request.files.get('image')

            updates = []
            params = []
            if username:
                updates.append("username = %s")
                params.append(username)
            if email:
                updates.append("email = %s")
                params.append(email)
            if password:
                hashed_password = generate_password_hash(password)
                updates.append("password = %s")
                params.append(hashed_password)
            if phone_number:
                updates.append("phone_number = %s")
                params.append(phone_number)

            if updates:
                params.append(user_id)
                query = f"UPDATE users SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)

            if face_image:
                # معالجة صورة الوجه الجديدة
                image_data = face_image.read()
                if not image_data:
                    return jsonify({'message': 'Invalid or empty image file'}), 400

                import face_recognition
                temp_file = 'temp_image.jpg'
                with open(temp_file, 'wb') as f:
                    f.write(image_data)
                image = face_recognition.load_image_file(temp_file)
                encodings = face_recognition.face_encodings(image)
                os.remove(temp_file)

                if not encodings:
                    return jsonify({'message': 'No face detected in the image'}), 400

                encoding_data = pickle.dumps(encodings[0])
                query = """
                    UPDATE face_encodings
                    SET encoding_data = %s, image_data = %s, reference_image_path = %s
                    WHERE user_id = %s
                """
                cursor.execute(query, (encoding_data, image_data, f'user_{user_id}_face.jpg', user_id))

            db.commit()
            print(f"[Update Profile] Profile updated for user_id {user_id}")
            return jsonify({'message': 'Profile updated'}), 200
        except mysql.connector.Error as err:
            db.rollback()
            return jsonify({'message': f'Database error: {str(err)}'}), 500
        finally:
            cursor.close()
            db.close()

# مسار إدارة المستخدمين (للمشرفين)
@app.route('/api/admin/users', methods=['GET', 'POST'])
def admin_users():
    # التحقق من التوكن
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = decode_token(token)
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # التحقق من صلاحية المشرف
        query = "SELECT role FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Forbidden'}), 403

        if request.method == 'GET':
            # استرجاع قائمة المستخدمين
            query = "SELECT id, username, email, phone_number FROM users"
            cursor.execute(query)
            users = cursor.fetchall()
            return jsonify(users), 200
        elif request.method == 'POST':
            # إضافة مستخدم جديد
            data = request.get_json()
            username = data.get('username', data.get('email'))
            email = data.get('email')
            phone_number = data.get('phoneNumber')
            password = data.get('password')

            if not all([username, email, password]):
                return jsonify({'message': 'Username, email, and password are required'}), 400

            query = "SELECT id FROM users WHERE email = %s"
            cursor.execute(query, (email,))
            if cursor.fetchone():
                return jsonify({'message': 'Email already exists'}), 400

            hashed_password = generate_password_hash(password)
            query = """
                INSERT INTO users (username, email, password, phone_number, role)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(query, (username, email, hashed_password, phone_number, 'user'))
            db.commit()
            print(f"[Admin] Added new user {username}")
            return jsonify({'message': 'User added'}), 200
    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500
    finally:
        cursor.close()
        db.close()

# مسار تعديل أو حذف مستخدم (للمشرفين)
@app.route('/api/admin/users/<int:user_id>', methods=['DELETE', 'PUT'])
def admin_users_update(user_id):
    # التحقق من التوكن
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id_admin = decode_token(token)
    if not user_id_admin:
        return jsonify({'message': 'Unauthorized'}), 401

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # التحقق من صلاحية المشرف
        query = "SELECT role FROM users WHERE id = %s"
        cursor.execute(query, (user_id_admin,))
        user = cursor.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Forbidden'}), 403

        if request.method == 'DELETE':
            # حذف المستخدم
            query = "DELETE FROM users WHERE id = %s"
            cursor.execute(query, (user_id,))
            db.commit()
            print(f"[Admin] Deleted user_id {user_id}")
            return jsonify({'message': 'User deleted'}), 200
        elif request.method == 'PUT':
            # تحديث بيانات المستخدم
            data = request.get_json()
            username = data.get('username')
            email = data.get('email')
            phone_number = data.get('phoneNumber')

            if not all([username, email]):
                return jsonify({'message': 'Username and email are required'}), 400

            query = "SELECT id FROM users WHERE email = %s AND id != %s"
            cursor.execute(query, (email, user_id))
            if cursor.fetchone():
                return jsonify({'message': 'Email already exists'}), 400

            query = """
                UPDATE users 
                SET username = %s, email = %s, phone_number = %s 
                WHERE id = %s
            """
            cursor.execute(query, (username, email, phone_number, user_id))
            db.commit()
            print(f"[Admin] Updated user_id {user_id}")
            return jsonify({'message': 'User updated'}), 200
    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500
    finally:
        cursor.close()
        db.close()

# مسار إدارة المحاضرات (للمشرفين)
@app.route('/api/admin/lectures', methods=['GET', 'POST'])
def admin_lectures():
    # التحقق من التوكن
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = decode_token(token)
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # التحقق من صلاحية المشرف
        query = "SELECT role FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Forbidden'}), 403

        if request.method == 'GET':
            # استرجاع قائمة المحاضرات
            query = """
                SELECT lecture_id AS id, name_of_user AS name, topic, date
                FROM lectures
            """
            cursor.execute(query)
            lectures = cursor.fetchall()
            return jsonify(lectures), 200
        elif request.method == 'POST':
            # إضافة محاضرة جديدة
            data = request.get_json()
            name = data.get('name')
            topic = data.get('topic')
            date = data.get('date')

            if not all([name, topic, date]):
                return jsonify({'message': 'Name, topic, and date are required'}), 400

            query = """
                INSERT INTO lectures (user_id, name_of_user, topic, date)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, name, topic, date))
            db.commit()
            print(f"[Admin] Added new lecture for user_id {user_id}")
            return jsonify({'message': 'Lecture added'}), 200
    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500
    finally:
        cursor.close()
        db.close()

# مسار تعديل أو حذف محاضرة (للمشرفين)
@app.route('/api/admin/lectures/<int:lecture_id>', methods=['DELETE', 'PUT'])
def admin_lectures_update(lecture_id):
    # التحقق من التوكن
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = decode_token(token)
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401

    # الاتصال بقاعدة البيانات
    db = get_mysql_connection()
    cursor = db.cursor(dictionary=True)
    try:
        # التحقق من صلاحية المشرف
        query = "SELECT role FROM users WHERE id = %s"
        cursor.execute(query, (user_id,))
        user = cursor.fetchone()
        if not user or user['role'] != 'admin':
            return jsonify({'message': 'Forbidden'}), 403

        if request.method == 'DELETE':
            # حذف المحاضرة
            query = "DELETE FROM lectures WHERE lecture_id = %s"
            cursor.execute(query, (lecture_id,))
            db.commit()
            print(f"[Admin] Deleted lecture_id {lecture_id}")
            return jsonify({'message': 'Lecture deleted'}), 200
        elif request.method == 'PUT':
            # تحديث بيانات المحاضرة
            data = request.get_json()
            name = data.get('name')
            topic = data.get('topic')
            date = data.get('date')

            if not all([name, topic, date]):
                return jsonify({'message': 'Name, topic, and date are required'}), 400

            query = """
                UPDATE lectures 
                SET name_of_user = %s, topic = %s, date = %s 
                WHERE lecture_id = %s
            """
            cursor.execute(query, (name, topic, date, lecture_id))
            db.commit()
            print(f"[Admin] Updated lecture_id {lecture_id}")
            return jsonify({'message': 'Lecture updated'}), 200
    except mysql.connector.Error as err:
        return jsonify({'message': f'Database error: {str(err)}'}), 500
    finally:
        cursor.close()
        db.close()

# مسار بدء التحكم بالإيماءات
@app.route('/api/start_gesture_control', methods=['POST'])
def start_gesture_control():
    global gesture_controller, controller_thread
    # استرجاع معرف المحاضرة
    lecture_id = request.form.get('lecture_id')
    # التحقق من التوكن
    token = request.headers.get('Authorization', '').replace('Bearer ', '')
    user_id = decode_token(token)
    if not user_id:
        return jsonify({'message': 'Unauthorized'}), 401
    if not lecture_id:
        return jsonify({'message': 'Lecture ID is required'}), 400

    # إيقاف أي تحكم سابق بالإيماءات
    if gesture_controller:
        gesture_controller.stop()
        if controller_thread:
            controller_thread.join(timeout=2.0)
            if controller_thread.is_alive():
                print("[Gesture Control] Warning: Controller thread did not terminate properly")

    # إنشاء كائن للتحكم بالإيماءات
    gesture_controller = GestureFaceVolumeController(app, lecture_id=lecture_id, user_id=user_id)

    # دالة لتشغيل معالجة الإيماءات
    def run_controller():
        with app.app_context():
            while gesture_controller.running:
                # معالجة إطار الفيديو
                frame, authorized, volume = gesture_controller.process_frame()
                if frame is not None:
                    # تحويل الإطار إلى صيغة JPEG
                    ret, buffer = cv2.imencode('.jpg', frame)
                    frame_data = buffer.tobytes()
                    # وضع الإطار في قائمة الانتظار
                    frame_queue.put(frame_data)
                    # إرسال تحديثات الصوت والتفويض عبر WebSocket
                    socketio.emit('update', {
                        'volume': volume,
                        'authorized': authorized
                    })

    # بدء التحكم بالإيماءات
    gesture_controller.running = True
    controller_thread = threading.Thread(target=run_controller)
    controller_thread.start()
    print(f"[Gesture Control] Started for lecture_id {lecture_id} by user_id {user_id}")
    return jsonify({'message': 'Gesture control started'}), 200

# مسار إيقاف التحكم بالإيماءات
@app.route('/api/stop_gesture_control', methods=['POST'])
def stop_gesture_control():
    global gesture_controller, controller_thread
    # إيقاف التحكم بالإيماءات
    if gesture_controller:
        gesture_controller.stop()
        if controller_thread:
            controller_thread.join(timeout=2.0)
            if controller_thread.is_alive():
                print("[Gesture Control] Warning: Controller thread did not terminate properly")
        gesture_controller = None
        controller_thread = None
    print("[Gesture Control] Stopped")
    return jsonify({'message': 'Gesture control stopped'}), 200

# مسار بث الفيديو (Video Feed)
@app.route('/video_feed')
def video_feed():
    # دالة لتوليد إطارات الفيديو
    def generate():
        while True:
            try:
                # استرجاع إطار من قائمة الانتظار
                frame = frame_queue.get(timeout=1)
                # إرسال الإطار بصيغة multipart
                yield (b'--frame\r\n'
                       b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            except queue.Empty:
                continue
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# معالجة اتصال WebSocket
@socketio.on('connect')
def handle_connect():
    print('[WebSocket] Client connected')

# معالجة انقطاع اتصال WebSocket
@socketio.on('disconnect')
def handle_disconnect():
    print('[WebSocket] Client disconnected')

# تشغيل التطبيق
if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
    # تشغيل الخادم على المنفذ 5000 مع وضع التصحيح (Debug Mode)