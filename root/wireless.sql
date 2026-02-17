CREATE DATABASE wireless;
USE wireless;

CREATE TABLE users (
    id INT PRIMARY KEY AUTO_INCREMENT,
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    password VARCHAR(255) NOT NULL,
    phone_number VARCHAR(20),
    role ENUM('user', 'admin') DEFAULT 'user',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE face_encodings (
    face_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    encoding_data MEDIUMBLOB, --  16 MB 
    image_data MEDIUMBLOB NOT NULL, --  16 MB
    reference_image_path VARCHAR(255),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE lectures (
    lecture_id INT PRIMARY KEY AUTO_INCREMENT,
    user_id INT NOT NULL,
    name_of_user VARCHAR(50) NOT NULL,
    topic VARCHAR(100) NOT NULL,
    date DATE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

CREATE TABLE volume_control_history (
    volume_id INT PRIMARY KEY AUTO_INCREMENT,
    lecture_id INT NOT NULL,
    user_id INT NOT NULL,
    volume_level INT NOT NULL CHECK (volume_level BETWEEN 0 AND 100),
    gesture_detected VARCHAR(50),
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (lecture_id) REFERENCES lectures(lecture_id) ON DELETE CASCADE,
    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);
