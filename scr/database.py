# استيراد المكتبات اللازمة
import mysql.connector
# مكتبة للتعامل مع قواعد بيانات MySQL (MySQL Connector)
from flask import current_app
# استيراد كائن current_app للوصول إلى إعدادات تطبيق Flask الحالي

# دالة لإنشاء اتصال بقاعدة البيانات
def get_db_connection():
    try:
        # محاولة إنشاء اتصال بقاعدة البيانات باستخدام إعدادات التطبيق
        return mysql.connector.connect(**current_app.config['MYSQL_CONFIG'])
        # **current_app.config['MYSQL_CONFIG']: فك تجميع إعدادات MySQL (مثل host, user, password, database)
    except mysql.connector.Error as err:
        # معالجة الأخطاء أثناء الاتصال بقاعدة البيانات
        print(f"Error connecting to database: {str(err)}")
        # طباعة رسالة الخطأ للتصحيح
        raise
        # إعادة إلقاء الاستثناء ليتم التعامل معه في الدوال المستدعية

# دالة لإدارة اتصال MySQL المعاد استخدامه
def get_mysql_connection():
    # التحقق مما إذا كان هناك اتصال موجود ومتصل
    if not hasattr(current_app, 'mysql') or not current_app.mysql.is_connected():
        # إذا لم يكن هناك اتصال أو انقطع الاتصال
        current_app.mysql = get_db_connection()
        # إنشاء اتصال جديد وتخزينه في كائن التطبيق
    return current_app.mysql
    # إرجاع الاتصال الحالي (MySQL Connection)
