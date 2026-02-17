# استيراد مكتبات معالجة الصور والفيديو
import cv2  # مكتبة OpenCV لمعالجة الصور والفيديو (Computer Vision)
import face_recognition  # مكتبة للتعرف على الوجوه (Face Recognition)
import mediapipe as mp  # مكتبة MediaPipe لتتبع اليد والوجه (Hand Tracking, Face Detection)
from math import hypot  # دالة لحساب المسافة بين نقطتين (Euclidean Distance)
import numpy as np  # مكتبة للعمليات الرياضية والمصفوفات (Numerical Operations)
import pickle  # مكتبة لتحميل وحفظ البيانات المسلسلة (Serialization)
import os  # مكتبة للتعامل مع نظام الملفات (File System Operations)
import tempfile  # مكتبة لإنشاء ملفات مؤقتة (Temporary Files)
from database import get_mysql_connection  # مكتبة مخصصة للاتصال بقاعدة بيانات MySQL

# استيراد مكتبات التحكم بمستوى الصوت
from ctypes import cast, POINTER  # مكتبة للتعامل مع أنواع البيانات في واجهات Windows
from comtypes import CLSCTX_ALL  # مكتبة للتعامل مع COM في Windows
from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume  # مكتبة للتحكم بمستوى الصوت في النظام

# تعريف الكلاس الرئيسي للتحكم بحركات اليد والتعرف على الوجه
class GestureFaceVolumeController:
    # دالة التهيئة (Constructor) لإعداد الكائن
    def __init__(self, app, lecture_id=None, user_id=None):
        # تخزين متغير التطبيق (Flask App) لاستخدامه لاحقاً
        self.app = app
        # تهيئة مكتبة MediaPipe لتتبع اليد (Hand Tracking)
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            max_num_hands=1,  # الحد الأقصى لعدد الأيدي المكتشفة
            min_detection_confidence=0.7,  # الحد الأدنى لثقة الكشف
            min_tracking_confidence=0.7  # الحد الأدنى لثقة التتبع
        )

        # تهيئة مكتبة MediaPipe للكشف عن الوجه (Face Detection)
        self.mp_face_detection = mp.solutions.face_detection
        self.face_detection = self.mp_face_detection.FaceDetection(min_detection_confidence=0.5)
        # أداة الرسم من MediaPipe لرسم النقاط على الصورة
        self.mp_draw = mp.solutions.drawing_utils

        # تهيئة كاميرا الفيديو (Webcam)
        self.cap = cv2.VideoCapture(0)
        if not self.cap.isOpened():
            raise RuntimeError("Could not open video capture")  # خطأ إذا لم تُفتح الكاميرا

        # إعداد دقة وسرعة الكاميرا
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)  # عرض الصورة
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)  # ارتفاع الصورة
        self.cap.set(cv2.CAP_PROP_FPS, 30)  # عدد الإطارات في الثانية (Frames Per Second)

        # تخزين معرف المحاضرة ومعرف المستخدم
        self.lecture_id = lecture_id
        self.user_id = user_id
        # متغير لتفعيل التعرف على الوجه (Face Recognition)
        self.face_recognition_active = False
        # متغير لتخزين مستوى الصوت الحالي (Volume Level)
        self.current_volume = 50.0  # قيمة افتراضية 50%
        # متغير لتخزين آخر قيمة صوت محفوظة
        self.last_saved_volume = 50.0
        # متغير للتحكم بحالة التشغيل
        self.running = False
        # متغير للتحقق من اكتشاف مستخدم مخول
        self.authorized_user_detected = False
        # قائمة لتخزين بيانات التعرف على الوجه (Face Encodings)
        self.authorized_encodings = []
        # عداد الإطارات لتقليل معالجة التعرف على الوجه
        self.frame_counter = 0

        # تحميل بيانات التعرف على الوجه
        self.load_authorized_encodings()
        # تهيئة التحكم بمستوى الصوت في النظام
        self.init_system_volume_control()

    # دالة لتهيئة واجهة التحكم بمستوى الصوت في النظام
    def init_system_volume_control(self):
        try:
            # الحصول على واجهة مكبرات الصوت (Speakers Interface)
            devices = AudioUtilities.GetSpeakers()
            # تفعيل واجهة التحكم بالصوت
            interface = devices.Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            # تحويل الواجهة إلى نوع مناسب
            self.volume_interface = cast(interface, POINTER(IAudioEndpointVolume))
            print("[System Volume] Initialized volume interface.")
        except Exception as e:
            print(f"[System Volume] Failed to initialize volume interface: {str(e)}")
            raise

    # دالة لضبط مستوى الصوت في النظام
    def set_system_volume(self, level):
        try:
            # تحويل مستوى الصوت من نطاق 0-100 إلى 0.0-1.0
            volume_level = level / 100
            # ضبط مستوى الصوت باستخدام الواجهة
            self.volume_interface.SetMasterVolumeLevelScalar(volume_level, None)
            print(f"[System Volume] Volume set to {level}%")
        except Exception as e:
            print(f"[System Volume] Error setting volume to {level}%: {str(e)}")

    # دالة لحفظ سجل تغييرات مستوى الصوت في قاعدة البيانات
    def save_volume_history(self, volume_level, gesture_detected):
        # التحقق من وجود معرف المحاضرة والمستخدم
        if not self.lecture_id or not self.user_id:
            print("[Save Volume History] Missing lecture_id or user_id, cannot save volume history")
            return

        # استخدام سياق التطبيق (Flask Context)
        with self.app.app_context():
            cursor = None
            try:
                # الاتصال بقاعدة البيانات
                cursor = get_mysql_connection().cursor()
                # استعلام لإدخال بيانات الصوت
                query = """
                    INSERT INTO volume_control_history (lecture_id, user_id, volume_level, gesture_detected)
                    VALUES (%s, %s, %s, %s)
                """
                cursor.execute(query, (self.lecture_id, self.user_id, int(volume_level), gesture_detected))
                # حفظ التغييرات
                get_mysql_connection().commit()
                print(f"[Save Volume History] Saved volume {volume_level}% for lecture {self.lecture_id}, user {self.user_id}")
            except Exception as e:
                print(f"[Save Volume History] Error saving volume history: {str(e)}")
                # التراجع عن التغييرات في حالة الخطأ
                get_mysql_connection().rollback()
            finally:
                # إغلاق المؤشر
                if cursor:
                    cursor.close()

    # دالة لتحميل بيانات التعرف على الوجه من قاعدة البيانات
    def load_authorized_encodings(self):
        # التحقق من وجود معرف المستخدم
        if not self.user_id:
            print("[Load Encodings] No user_id provided, cannot load encodings")
            return

        # استخدام سياق التطبيق
        with self.app.app_context():
            cursor = None
            try:
                # الاتصال بقاعدة البيانات
                cursor = get_mysql_connection().cursor()
                # استعلام لجلب بيانات الوجه
                query = """
                    SELECT u.id, fe.encoding_data, fe.reference_image_path, fe.image_data 
                    FROM users u
                    JOIN face_encodings fe ON u.id = fe.user_id
                    WHERE u.id = %s
                """
                cursor.execute(query, (self.user_id,))
                result = cursor.fetchone()

                # التحقق من وجود نتيجة
                if not result:
                    print(f"[Load Encodings] No encoding found for user_id {self.user_id}")
                    return

                # استخراج البيانات
                user_id, encoding_data, image_path, image_data = result
                if not image_data and not encoding_data:
                    print(f"[Load Encodings] No image or encoding data for user {user_id}")
                    return

                # إذا كانت بيانات التعرف موجودة
                if encoding_data:
                    try:
                        # تحميل البيانات المسلسلة
                        encoding = pickle.loads(encoding_data)
                        self.authorized_encodings.append({
                            'user_id': user_id,
                            'encoding': encoding,
                            'image_path': image_path,
                            'image_data': image_data
                        })
                        print(f"[Load Encodings] Successfully loaded encoding for user {user_id}")
                    except Exception as e:
                        print(f"[Load Encodings] Failed to unpickle encoding for user {user_id}: {str(e)}")
                else:
                    # إذا لم تكن البيانات موجودة، إعادة حسابها من الصورة
                    print(f"[Load Encodings] No encoding data for user {user_id}, recalculating from image")
                    with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as temp_file:
                        temp_file.write(image_data)
                        temp_file_path = temp_file.name

                    try:
                        # تحميل الصورة وحساب التعرف
                        image = face_recognition.load_image_file(temp_file_path)
                        encodings = face_recognition.face_encodings(image)
                        if encodings:
                            encoding = encodings[0]
                            self.authorized_encodings.append({
                                'user_id': user_id,
                                'encoding': encoding,
                                'image_path': image_path,
                                'image_data': image_data
                            })
                            # تحديث قاعدة البيانات بالبيانات الجديدة
                            new_encoding_data = pickle.dumps(encoding)
                            update_query = "UPDATE face_encodings SET encoding_data = %s WHERE user_id = %s"
                            cursor.execute(update_query, (new_encoding_data, user_id))
                            get_mysql_connection().commit()
                            print(f"[Load Encodings] Recalculated and updated encoding for user {user_id}")
                        else:
                            print(f"[Load Encodings] No face detected in image for user {user_id}")
                    finally:
                        # حذف الملف المؤقت
                        if os.path.exists(temp_file_path):
                            os.unlink(temp_file_path)
            except Exception as e:
                print(f"[Load Encodings] Error loading face encodings from database: {str(e)}")
                raise
            finally:
                # إغلاق المؤشر
                if cursor:
                    cursor.close()
        
    # دالة للكشف عن إيماءة النصر (Victory Sign)
    def detect_victory_sign(self, hand_landmarks):
        if not hand_landmarks:
            return False
       
        # استخراج نقاط اليد (Landmarks)
        landmarks = hand_landmarks.landmark
        hand = self.mp_hands.HandLandmark

        # التحقق من تمدد الأصابع المناسبة لإيماءة النصر
        index_extended = landmarks[hand.INDEX_FINGER_TIP].y < landmarks[hand.INDEX_FINGER_PIP].y
        middle_extended = landmarks[hand.MIDDLE_FINGER_TIP].y < landmarks[hand.MIDDLE_FINGER_PIP].y
        ring_folded = landmarks[hand.RING_FINGER_TIP].y > landmarks[hand.RING_FINGER_PIP].y
        pinky_folded = landmarks[hand.PINKY_TIP].y > landmarks[hand.PINKY_PIP].y
        thumb_folded = landmarks[hand.THUMB_TIP].x > landmarks[hand.INDEX_FINGER_MCP].x

        # إيماءة النصر: السبابة والوسطى ممدودتان، بقية الأصابع مطوية
        victory_detected = index_extended and middle_extended and ring_folded and pinky_folded and thumb_folded
        if victory_detected:
            print("[Gesture] Victory sign detected")
        return victory_detected
        
    # دالة لمعالجة كل إطار من الفيديو
    def process_frame(self):
        # قراءة إطار من الكاميرا
        success, img = self.cap.read()
        if not success:
            print("[Process Frame] Failed to capture frame from camera")
            return None, False, self.current_volume

        # تحويل الصورة إلى RGB للمعالجة
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img.flags.writeable = False

        # معالجة اليد والوجه باستخدام MediaPipe
        hand_results = self.hands.process(img_rgb)
        face_results = self.face_detection.process(img_rgb)
        img.flags.writeable = True
   
        # التحقق من إيماءة النصر
        victory_detected = False
        if hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                if self.detect_victory_sign(hand_landmarks):
                    self.face_recognition_active = True
                    victory_detected = True
                    break

        # التحقق من المستخدم المخول
        authorized = self.authorized_user_detected
        if self.face_recognition_active and self.authorized_encodings:
            self.frame_counter += 1
            # معالجة التعرف على الوجه كل 5 إطارات
            if self.frame_counter % 5 == 0:
                # اكتشاف مواقع الوجوه
                face_locations = face_recognition.face_locations(img_rgb)
                # استخراج بيانات التعرف على الوجه
                current_encodings = face_recognition.face_encodings(img_rgb, face_locations)
                print(f"[Process Frame] Frame {self.frame_counter}: Detected {len(face_locations)} faces")

                # التحقق من وجود وجوه
                if face_locations and current_encodings:
                    # اختيار أكبر وجه
                    largest_face_index = np.argmax([(loc[2] - loc[0]) * (loc[1] - loc[3]) for loc in face_locations])
                    face_area = (face_locations[largest_face_index][2] - face_locations[largest_face_index][0]) * \
                                (face_locations[largest_face_index][1] - face_locations[largest_face_index][3])
                    # تجاهل الوجوه الصغيرة (ربما أشخاص في الخلفية)
                    if face_area < 10000:
                        print("[Process Frame] Face too small, likely background person, ignoring")
                        return img, authorized, self.current_volume
  
                    # مقارنة الوجه مع البيانات المخزنة
                    face_encoding = current_encodings[largest_face_index]
                    matches = face_recognition.compare_faces(
                        [enc['encoding'] for enc in self.authorized_encodings],
                        face_encoding,
                        tolerance=0.5
                    )
                    if any(matches):
                        authorized = True
                        print(f"[Process Frame] Authorized user {self.user_id} detected")
                    else:
                        print("[Process Frame] No authorized user matched")

        self.authorized_user_detected = authorized

        # حساب المسافة بين الإبهام والسبابة لضبط الصوت
        thumb_index_distance = 0
        if authorized and hand_results.multi_hand_landmarks:
            for hand_landmarks in hand_results.multi_hand_landmarks:
                # استخراج إحداثيات نقاط اليد
                landmarks = [[id, int(lm.x * img.shape[1]), int(lm.y * img.shape[0])]
                             for id, lm in enumerate(hand_landmarks.landmark)]
                if landmarks:
                    x1, y1 = landmarks[4][1], landmarks[4][2]  # الإبهام
                    x2, y2 = landmarks[8][1], landmarks[8][2]  # السبابة

                    # حساب المسافة بين الإبهام والسبابة
                    thumb_index_distance = hypot(x2 - x1, y2 - y1)
                    # رسم خط ودوائر على الصورة
                    cv2.line(img, (x1, y1), (x2, y2), (255, 0, 0), 2)
                    cv2.circle(img, (x1, y1), 5, (0, 255, 0), -1)
                    cv2.circle(img, (x2, y2), 5, (0, 255, 0), -1)

                    # تحويل المسافة إلى مستوى صوت (0-100)
                    new_volume = np.interp(thumb_index_distance, [15, 80], [0, 100])
                    new_volume = max(0, min(100, new_volume))

                    # حفظ مستوى الصوت إذا تغير بشكل كبير
                    if abs(new_volume - self.last_saved_volume) >= 1:
                        self.current_volume = new_volume
                        self.set_system_volume(int(new_volume))
                        gesture = "Thumb-Index Distance" if thumb_index_distance > 0 else "None"
                        self.save_volume_history(new_volume, gesture)
                        self.last_saved_volume = new_volume

        # إضافة نص الحالة على الصورة
        status_text = f"Auth: {'Yes' if authorized else 'No'} | Vol: {int(self.current_volume)}% | Dist: {int(thumb_index_distance)}px"
        cv2.putText(img, status_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 0), 2)

        return img, authorized, self.current_volume

    # دالة لتشغيل النظام
    def run(self):
        self.running = True
        try:
            while self.running:
                # معالجة كل إطار
                img, authorized, volume = self.process_frame()
                if img is not None:
                    # عرض الصورة
                    cv2.imshow("Gesture and Face Control", img)
                    # الخروج عند الضغط على 'q'
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        break
        finally:
            # إيقاف الكاميرا وإغلاق النوافذ
            self.cap.release()
            cv2.destroyAllWindows()

    # دالة لإيقاف النظام
    def stop(self):
        self.running = False
        if self.cap.isOpened():
            self.cap.release()
        cv2.destroyAllWindows()