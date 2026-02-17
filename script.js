// تعريف المتغيرات العامة
let currentUser = null;
// متغير لتخزين بيانات المستخدم الحالي (Current User)
let currentLectureId = null;
// متغير لتخزين معرف المحاضرة الحالية (Lecture ID)
let socket = null;
// متغير لتخزين كائن WebSocket للتفاعل في الوقت الفعلي

// دالة لعرض صفحة معينة بناءً على معرفها (Page ID)
function showPage(pageId) {
    // قائمة الصفحات المحمية التي تتطلب تسجيل الدخول
    const protectedPages = ['page1', 'page2', 'page3', 'account-page', 'admin-dashboard'];
    // التحقق مما إذا كانت الصفحة محمية ولم يتم تسجيل الدخول
    if (protectedPages.includes(pageId) && !isAuthenticated()) {
        pageId = 'signin-page';
        // إعادة التوجيه إلى صفحة تسجيل الدخول
        alert('Please sign in to access this page');
        // عرض تنبيه للمستخدم
    }

    // إخفاء جميع الصفحات
    document.querySelectorAll('.page').forEach(page => {
        page.classList.remove('active');
        // إزالة الفئة active لإخفاء الصفحة
    });

    // إظهار الصفحة المطلوبة
    document.getElementById(pageId).classList.add('active');
    // إضافة الفئة active لعرض الصفحة

    // تنفيذ إجراءات إضافية بناءً على الصفحة
    if (pageId === 'page3') {
        startGestureControl();
        // بدء التحكم بالإيماءات عند عرض صفحة الكاميرا
    } else if (pageId === 'account-page' && isAuthenticated()) {
        loadUserProfile();
        // تحميل بيانات الملف الشخصي عند عرض صفحة الحساب
    } else if (pageId === 'admin-dashboard' && isAuthenticated()) {
        loadAdminData();
        // تحميل بيانات لوحة التحكم الإدارية
    }
}

// دالة للتحقق مما إذا كان المستخدم مسجل الدخول
function isAuthenticated() {
    return !!localStorage.getItem('auth_token');
    // إرجاع true إذا كان هناك توكن مخزن في localStorage
}

// دالة تسجيل الخروج
function logout() {
    localStorage.removeItem('auth_token');
    // إزالة التوكن من localStorage
    localStorage.removeItem('user');
    // إزالة بيانات المستخدم
    showPage('home-page');
    // إعادة التوجيه إلى الصفحة الرئيسية
}

// معالجة إرسال نموذج التسجيل (Signup Form)
document.getElementById('signup-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    // منع السلوك الافتراضي لإرسال النموذج

    const formData = new FormData(this);
    // إنشاء كائن FormData لجمع بيانات النموذج
    const username = formData.get('username');
    const email = formData.get('email');
    const password = formData.get('password');
    const phoneNumber = formData.get('phoneNumber');

    // تعبيرات منتظمة للتحقق من المدخلات (Regular Expressions)
    const englishLettersAndNumbers = /^[A-Za-z0-9]+$/;
    const englishEmail = /^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}$/;
    const englishPassword = /^[A-Za-z0-9!@#$%^&*]+$/;
    const digitsOnly = /^[0-9]+$/;

    // التحقق من صحة المدخلات
    if (!englishLettersAndNumbers.test(username)) {
        alert('Username must contain only English letters and numbers.');
        return;
    }
    if (!englishEmail.test(email)) {
        alert('Email must contain only English characters.');
        return;
    }
    if (!englishPassword.test(password)) {
        alert('Password must contain only English letters, numbers, and allowed special characters (!@#$%^&*).');
        return;
    }
    if (!digitsOnly.test(phoneNumber)) {
        alert('Phone number must contain only digits.');
        return;
    }

    try {
        // إرسال طلب التسجيل إلى الخادم
        const response = await fetch('/api/auth/signup', {
            method: 'POST',
            body: formData
            // إرسال بيانات النموذج كـ FormData
        });

        const data = await response.json();
        // تحويل الرد إلى JSON

        if (response.ok) {
            alert('Signup successful! Please sign in.');
            showPage('signin-page');
            // عرض تنبيه وإعادة التوجيه إلى صفحة تسجيل الدخول
        } else {
            alert(data.message || 'Signup failed');
            // عرض رسالة الخطأ
        }
    } catch (error) {
        console.error('Signup error:', error);
        alert('An error occurred during signup');
        // معالجة الأخطاء العامة
    }
});

// معالجة إرسال نموذج تسجيل الدخول (Signin Form)
document.getElementById('signin-form').addEventListener('submit', async function(e) {
    e.preventDefault();
    // منع السلوك الافتراضي

    const formData = new FormData(this);
    const formDataObj = {
        email: formData.get('email'),
        password: formData.get('password')
    };
    // إنشاء كائن يحتوي على بيانات النموذج

    try {
        // إرسال طلب تسجيل الدخول
        const response = await fetch('/api/auth/signin', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formDataObj)
            // إرسال البيانات كـ JSON
        });

        const data = await response.json();

        if (response.ok) {
            localStorage.setItem('auth_token', data.token);
            // تخزين التوكن في localStorage
            localStorage.setItem('user', JSON.stringify(data.user));
            // تخزين بيانات المستخدم
            currentUser = data.user;
            // تحديث متغير المستخدم الحالي

            if (data.user.role === 'admin') {
                showPage('admin-dashboard');
                // إعادة توجيه المشرف إلى لوحة التحكم
            } else {
                showPage('page1');
                // إعادة توجيه المستخدم العادي إلى صفحة التعليمات
            }
        } else {
            alert(data.message || 'Sign in failed');
            // عرض رسالة الخطأ
        }
    } catch (error) {
        console.error('Sign in error:', error);
        alert('An error occurred during sign in');
        // معالجة الأخطاء
    }
});

// معالجة إرسال نموذج نسيان كلمة المرور (Forgot Password Form)
document.getElementById('forgot-password-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const email = this.email.value;
    const messageElement = document.getElementById('reset-message');
    // عنصر لعرض رسائل الخطأ أو النجاح

    try {
        // إرسال طلب إعادة تعيين كلمة المرور
        const response = await fetch('/api/auth/forgot-password', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ email })
        });

        const data = await response.json();

        messageElement.textContent = data.message;
        messageElement.style.display = 'block';
        // عرض رسالة الرد

        this.reset();
        // إعادة تعيين النموذج
    } catch (error) {
        console.error('Forgot password error:', error);
        messageElement.textContent = 'An error occurred. Please try again later.';
        messageElement.style.display = 'block';
        // معالجة الأخطاء
    }
});

// معالجة إرسال نموذج إنشاء محاضرة (Lecture Form)
document.getElementById('lecture-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    if (!isAuthenticated()) {
        alert('Please sign in to create a lecture');
        showPage('signin-page');
        return;
        // التحقق من تسجيل الدخول
    }

    const formData = new FormData(this);
    const formDataObj = {
        userName: formData.get('userName'),
        topic: formData.get('topic'),
        date: formData.get('date')
    };

    try {
        // إرسال طلب إنشاء محاضرة
        const response = await fetch('/api/lectures', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
                // إضافة التوكن للتحقق
            },
            body: JSON.stringify(formDataObj)
        });

        const data = await response.json();

        if (response.ok) {
            currentLectureId = data.lecture_id;
            // تخزين معرف المحاضرة
            showPage('page3');
            // الانتقال إلى صفحة الكاميرا
        } else {
            alert(data.message || 'Failed to create lecture');
        }
    } catch (error) {
        console.error('Lecture creation error:', error);
        alert('An error occurred while creating the lecture');
    }
});

// معالجة إرسال نموذج تحديث الحساب (Account Form)
document.getElementById('account-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    if (!isAuthenticated()) {
        alert('Please sign in to update your profile');
        showPage('signin-page');
        return;
    }

    const formData = new FormData(this);

    try {
        // إرسال طلب تحديث الملف الشخصي
        const response = await fetch('/api/user/profile', {
            method: 'PUT',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: formData
        });

        const data = await response.json();

        if (response.ok) {
            alert('Profile updated successfully');
            const user = JSON.parse(localStorage.getItem('user'));
            user.username = formData.get('username') || user.username;
            user.email = formData.get('email') || user.email;
            localStorage.setItem('user', JSON.stringify(user));
            // تحديث بيانات المستخدم في localStorage
            loadUserProfile();
            // إعادة تحميل الملف الشخصي
        } else {
            alert(data.message || 'Failed to update profile');
        }
    } catch (error) {
        console.error('Profile update error:', error);
        alert('An error occurred while updating your profile');
    }
});

// دالة لتحميل بيانات الملف الشخصي
async function loadUserProfile() {
    if (!isAuthenticated()) {
        return;
    }

    try {
        // استرجاع بيانات الملف الشخصي
        const response = await fetch('/api/user/profile', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        });

        if (response.ok) {
            const profile = await response.json();

            const form = document.getElementById('account-form');
            form.username.value = profile.username;
            form.email.value = profile.email;
            form.phoneNumber.value = profile.phone_number || '';
            // تعبئة النموذج ببيانات المستخدم

            const imagePreview = document.getElementById('account-image-preview');
            if (profile.image) {
                imagePreview.innerHTML = `<img src="${profile.image}" alt="Profile">`;
                // عرض صورة الملف الشخصي
            } else {
                imagePreview.innerHTML = '';
            }
        } else {
            localStorage.removeItem('auth_token');
            localStorage.removeItem('user');
            showPage('signin-page');
            // تسجيل الخروج في حالة فشل الطلب
        }
    } catch (error) {
        console.error('Error fetching profile:', error);
    }
}

// دالة لتحميل بيانات لوحة التحكم الإدارية
async function loadAdminData() {
    if (!isAuthenticated()) {
        return;
    }

    try {
        // استرجاع بيانات المستخدمين
        const usersResponse = await fetch('/api/admin/users', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        });

        // استرجاع بيانات المحاضرات
        const lecturesResponse = await fetch('/api/admin/lectures', {
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        });

        if (usersResponse.ok && lecturesResponse.ok) {
            const users = await usersResponse.json();
            const lectures = await lecturesResponse.json();

            document.getElementById('total-users').textContent = users.length;
            document.getElementById('total-lectures').textContent = lectures.length;
            // تحديث إجمالي المستخدمين والمحاضرات

            const usersTableBody = document.querySelector('#users-table tbody');
            usersTableBody.innerHTML = '';
            // إفراغ جدول المستخدمين

            users.forEach(user => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${user.username}</td>
                    <td>${user.email}</td>
                    <td>${user.phone_number || 'N/A'}</td>
                    <td>
                        <button onclick='editUser(${JSON.stringify(user)})'>Edit</button>
                        <button onclick="deleteUser(${user.id})">Delete</button>
                    </td>
                `;
                usersTableBody.appendChild(row);
                // إضافة صفوف لجدول المستخدمين
            });

            const lecturesTableBody = document.querySelector('#lectures-table tbody');
            lecturesTableBody.innerHTML = '';

            lectures.forEach(lecture => {
                const row = document.createElement('tr');
                row.innerHTML = `
                    <td>${lecture.name}</td>
                    <td>${lecture.topic}</td>
                    <td>${lecture.date}</td>
                    <td>
                        <button onclick='editLecture(${JSON.stringify(lecture)})'>Edit</button>
                        <button onclick="deleteLecture(${lecture.id})">Delete</button>
                    </td>
                `;
                lecturesTableBody.appendChild(row);
                // إضافة صفوف لجدول المحاضرات
            });
        } else {
            if (usersResponse.status === 401 || lecturesResponse.status === 401) {
                localStorage.removeItem('auth_token');
                localStorage.removeItem('user');
                showPage('signin-page');
                // تسجيل الخروج في حالة خطأ التفويض
            } else if (usersResponse.status === 403 || lecturesResponse.status === 403) {
                alert('You do not have permission to access the admin dashboard');
                showPage('page1');
                // إعادة التوجيه إذا لم يكن المستخدم مشرفًا
            }
        }
    } catch (error) {
        console.error('Error fetching admin data:', error);
    }
}

// دالة لبدء التحكم بالإيماءات
async function startGestureControl() {
    if (!currentLectureId) {
        alert('No lecture selected. Please create a lecture first.');
        showPage('page2');
        return;
        // التحقق من وجود محاضرة
    }

    // إنشاء اتصال WebSocket
    socket = io.connect('http://' + document.domain + ':' + location.port);

    socket.on('connect', function() {
        console.log('WebSocket connected');
        // تسجيل الاتصال الناجح
    });

    socket.on('update', function(data) {
        const gestureIndicator = document.getElementById('gesture-indicator');
        const volumeLevel = document.getElementById('volume-level');
        const volumePercentage = document.getElementById('volume-percentage');

        volumeLevel.style.width = `${data.volume}%`;
        volumePercentage.textContent = `${Math.round(data.volume)}%`;
        // تحديث شريط الصوت والنسبة المئوية

        gestureIndicator.textContent = data.authorized ? 'Authorized' : 'Not Authorized';
        gestureIndicator.style.display = 'block';
        gestureIndicator.style.backgroundColor = data.authorized ? 'rgba(0, 255, 0, 0.7)' : 'rgba(255, 0, 0, 0.7)';
        // تحديث مؤشر التفويض (Authorized/Not Authorized)

        setTimeout(() => {
            gestureIndicator.style.display = 'none';
        }, 2000);
        // إخفاء المؤشر بعد 2 ثانية
    });

    socket.on('disconnect', function() {
        console.log('WebSocket disconnected');
        // تسجيل انقطاع الاتصال
    });

    try {
        // إرسال طلب بدء التحكم بالإيماءات
        const response = await fetch('/api/start_gesture_control', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: `lecture_id=${currentLectureId}`
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || 'Failed to start gesture control');
        }
    } catch (error) {
        console.error('Error starting gesture control:', error);
        alert('Failed to start gesture control: ' + error.message);
        showPage('page2');
        // معالجة الأخطاء
    }
}

// دالة لإنهاء جلسة التحكم بالإيماءات
async function endSession() {
    if (socket) {
        socket.disconnect();
        socket = null;
        // قطع اتصال WebSocket
    }

    try {
        // إرسال طلب إيقاف التحكم بالإيماءات
        const response = await fetch('/api/stop_gesture_control', {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        });

        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.message || 'Failed to stop gesture control');
        }
    } catch (error) {
        console.error('Error stopping gesture control:', error);
    }

    currentLectureId = null;
    // إعادة تعيين معرف المحاضرة
    showPage('page2');
    // إعادة التوجيه إلى صفحة النموذج
}

// معالجة تحميل صورة الوجه في نموذج التسجيل
document.getElementById('face-image').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        // التحقق من نوع الملف
        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload a valid image file (JPEG, PNG, or GIF).');
            e.target.value = '';
            return;
        }

        // التحقق من حجم الملف (حد أقصى 5 ميغابايت)
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            alert('Image file size must be less than 5MB.');
            e.target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('image-preview');
            preview.innerHTML = `<img src="${e.target.result}" alt="Face preview">`;
            // عرض معاينة الصورة
        };
        reader.readAsDataURL(file);
        // قراءة الملف كـ Data URL
    }
});

// معالجة تحميل صورة الملف الشخصي في نموذج الحساب
document.getElementById('account-image').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        // التحقق من نوع الملف
        const validTypes = ['image/jpeg', 'image/png', 'image/gif'];
        if (!validTypes.includes(file.type)) {
            alert('Please upload a valid image file (JPEG, PNG, or GIF).');
            e.target.value = '';
            return;
        }

        // التحقق من حجم الملف
        const maxSize = 5 * 1024 * 1024; // 5MB
        if (file.size > maxSize) {
            alert('Image file size must be less than 5MB.');
            e.target.value = '';
            return;
        }

        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('account-image-preview');
            preview.innerHTML = `<img src="${e.target.result}" alt="Profile preview">`;
            // عرض معاينة الصورة
        };
        reader.readAsDataURL(file);
    }
});

// ملاحظة: هذا الحدث مكرر ويمكن دمجه مع السابق
document.getElementById('account-image').addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('account-image-preview');
            preview.innerHTML = `<img src="${e.target.result}" alt="Profile preview">`;
        };
        reader.readAsDataURL(file);
    }
});

// معالجة تحميل الصفحة (DOM Content Loaded)
document.addEventListener('DOMContentLoaded', function() {
    if (isAuthenticated()) {
        const user = JSON.parse(localStorage.getItem('user'));
        currentUser = user;
        // تحديث بيانات المستخدم الحالي

        const currentPage = document.querySelector('.page.active').id;
        if (['signin-page', 'signup-page', 'forgot-password-page'].includes(currentPage)) {
            if (user.role === 'admin') {
                showPage('admin-dashboard');
                // إعادة توجيه المشرف
            } else {
                showPage('page1');
                // إعادة توجيه المستخدم العادي
            }
        }
    }
});

// دالة لتعديل بيانات مستخدم في لوحة التحكم
function editUser(user) {
    const form = document.getElementById('edit-user-form');
    form.id.value = user.id;
    form.username.value = user.username;
    form.email.value = user.email;
    form.phoneNumber.value = user.phone_number || '';
    // تعبئة نموذج تعديل المستخدم
    document.getElementById('edit-user-modal').style.display = 'block';
    // إظهار النافذة المنبثقة
}

// دالة لإغلاق نافذة تعديل المستخدم
function closeEditUserModal() {
    document.getElementById('edit-user-modal').style.display = 'none';
    document.getElementById('edit-user-form').reset();
    // إخفاء النافذة وإعادة تعيين النموذج
}

// دالة لحذف مستخدم
function deleteUser(id) {
    if (confirm(`Are you sure you want to delete user with ID: ${id}?`)) {
        fetch(`/api/admin/users/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        })
        .then(response => {
            if (response.ok) {
                alert('User deleted successfully');
                loadAdminData();
                // إعادة تحميل البيانات بعد الحذف
            } else {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to delete user');
                });
            }
        })
        .catch(err => {
            console.error('Error deleting user:', err);
            alert(`Error: ${err.message}`);
        });
    }
}

// دالة لتعديل بيانات محاضرة
function editLecture(lecture) {
    const form = document.getElementById('edit-lecture-form');
    form.id.value = lecture.id;
    form.name.value = lecture.name;
    form.topic.value = lecture.topic;
    form.date.value = lecture.date.split('T')[0];
    // تعبئة نموذج تعديل المحاضرة
    document.getElementById('edit-lecture-modal').style.display = 'block';
}

// دالة لإغلاق نافذة تعديل المحاضرة
function closeEditLectureModal() {
    document.getElementById('edit-lecture-modal').style.display = 'none';
    document.getElementById('edit-lecture-form').reset();
}

// دالة لحذف محاضرة
function deleteLecture(id) {
    if (confirm(`Are you sure you want to delete lecture with ID: ${id}?`)) {
        fetch(`/api/admin/lectures/${id}`, {
            method: 'DELETE',
            headers: {
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            }
        })
        .then(response => {
            if (response.ok) {
                alert('Lecture deleted successfully');
                loadAdminData();
            } else {
                return response.json().then(data => {
                    throw new Error(data.message || 'Failed to delete lecture');
                });
            }
        })
        .catch(err => {
            console.error('Error deleting lecture:', err);
            alert(`Error: ${err.message}`);
        });
    }
}

// دالة لإظهار نافذة إضافة مستخدم
function showAddUserModal() {
    document.getElementById('add-user-modal').style.display = 'block';
}

// دالة لإغلاق نافذة إضافة مستخدم
function closeAddUserModal() {
    document.getElementById('add-user-modal').style.display = 'none';
    document.getElementById('add-user-form').reset();
}

// دالة لإظهار نافذة إضافة محاضرة
function showAddLectureModal() {
    document.getElementById('add-lecture-modal').style.display = 'block';
}

// دالة لإغلاق نافذة إضافة محاضرة
function closeAddLectureModal() {
    document.getElementById('add-lecture-modal').style.display = 'none';
    document.getElementById('add-lecture-form').reset();
}

// معالجة إرسال نموذج إضافة مستخدم
document.getElementById('add-user-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const userData = {
        username: formData.get('username'),
        email: formData.get('email'),
        phoneNumber: formData.get('phoneNumber'),
        password: formData.get('password')
    };

    try {
        // إرسال طلب إضافة مستخدم
        const response = await fetch('/api/admin/users', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify(userData)
        });

        const data = await response.json();
        if (response.ok) {
            alert('User added successfully');
            closeAddUserModal();
            loadAdminData();
        } else {
            alert(data.message || 'Failed to add user');
        }
    } catch (error) {
        console.error('Error adding user:', error);
        alert('An error occurred while adding the user');
    }
});

// معالجة إرسال نموذج تعديل مستخدم
document.getElementById('edit-user-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const userData = {
        id: formData.get('id'),
        username: formData.get('username'),
        email: formData.get('email'),
        phoneNumber: formData.get('phoneNumber')
    };

    try {
        // إرسال طلب تعديل المستخدم
        const response = await fetch(`/api/admin/users/${userData.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify(userData)
        });

        const data = await response.json();
        if (response.ok) {
            alert('User updated successfully');
            closeEditUserModal();
            loadAdminData();
        } else {
            alert(data.message || 'Failed to update user');
        }
    } catch (error) {
        console.error('Error updating user:', error);
        alert('An error occurred while updating the user');
    }
});

// معالجة إرسال نموذج إضافة محاضرة
document.getElementById('add-lecture-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const lectureData = {
        name: formData.get('name'),
        topic: formData.get('topic'),
        date: formData.get('date')
    };

    try {
        // إرسال طلب إضافة محاضرة
        const response = await fetch('/api/admin/lectures', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify(lectureData)
        });

        const data = await response.json();
        if (response.ok) {
            alert('Lecture added successfully');
            closeAddLectureModal();
            loadAdminData();
        } else {
            alert(data.message || 'Failed to add lecture');
        }
    } catch (error) {
        console.error('Error adding lecture:', error);
        alert('An error occurred while adding the lecture');
    }
});

// معالجة إرسال نموذج تعديل محاضرة
document.getElementById('edit-lecture-form').addEventListener('submit', async function(e) {
    e.preventDefault();

    const formData = new FormData(this);
    const lectureData = {
        id: formData.get('id'),
        name: formData.get('name'),
        topic: formData.get('topic'),
        date: formData.get('date')
    };

    try {
        // إرسال طلب تعديل المحاضرة
        const response = await fetch(`/api/admin/lectures/${lectureData.id}`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
            },
            body: JSON.stringify(lectureData)
        });

        const data = await response.json();
        if (response.ok) {
            alert('Lecture updated successfully');
            closeEditLectureModal();
            loadAdminData();
        } else {
            alert(data.message || 'Failed to update lecture');
        }
    } catch (error) {
        console.error('Error updating lecture:', error);
        alert('An error occurred while updating the lecture');
    }
});