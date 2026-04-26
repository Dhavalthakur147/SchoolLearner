CREATE DATABASE IF NOT EXISTS schoollearn
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE schoollearn;

CREATE TABLE IF NOT EXISTS student (
  student_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  full_name VARCHAR(160) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  grade VARCHAR(32) NULL,
  school VARCHAR(255) NULL,
  avatar_url VARCHAR(500) NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (student_id),
  UNIQUE KEY uq_student_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS subject (
  subject_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  subject_key VARCHAR(64) NOT NULL,
  subject_name VARCHAR(120) NOT NULL,
  is_enabled TINYINT(1) NOT NULL DEFAULT 1,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (subject_id),
  UNIQUE KEY uq_subject_key (subject_key),
  UNIQUE KEY uq_subject_name (subject_name)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS question (
  question_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  subject_id BIGINT UNSIGNED NOT NULL,
  question_text TEXT NOT NULL,
  option_a TEXT NOT NULL,
  option_b TEXT NOT NULL,
  option_c TEXT NOT NULL,
  option_d TEXT NOT NULL,
  answer_index TINYINT UNSIGNED NOT NULL,
  explanation TEXT NULL,
  source ENUM('base', 'custom') NOT NULL DEFAULT 'custom',
  base_key VARCHAR(64) NULL,
  is_deleted TINYINT(1) NOT NULL DEFAULT 0,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (question_id),
  UNIQUE KEY uq_question_base_key (base_key),
  KEY idx_question_subject (subject_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS result (
  result_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id BIGINT UNSIGNED NOT NULL,
  subject_id BIGINT UNSIGNED NOT NULL,
  score INT NOT NULL DEFAULT 0,
  total_questions INT NOT NULL DEFAULT 0,
  percentage DECIMAL(5,2) NOT NULL DEFAULT 0,
  attempted_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (result_id),
  KEY idx_result_student (student_id),
  KEY idx_result_subject (subject_id),
  KEY idx_result_attempted (attempted_at)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS admin (
  admin_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  username VARCHAR(120) NOT NULL,
  email VARCHAR(255) NOT NULL,
  password_hash VARCHAR(255) NOT NULL,
  created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (admin_id),
  UNIQUE KEY uq_admin_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS marks (
  mark_id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  student_id BIGINT UNSIGNED NOT NULL,
  exam_name VARCHAR(255) NOT NULL,
  subject_name VARCHAR(255) NOT NULL,
  score DECIMAL(6,2) NOT NULL,
  total DECIMAL(6,2) NOT NULL,
  percentage DECIMAL(5,2) NOT NULL,
  remarks TEXT NULL,
  recorded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  uploaded_by VARCHAR(255) NOT NULL,
  uploaded_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (mark_id),
  KEY idx_marks_student (student_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

INSERT INTO subject (subject_key, subject_name, is_enabled)
VALUES
  ('computer', 'Computer', 1),
  ('math', 'Mathematics', 1),
  ('science', 'Science', 1),
  ('english', 'English', 1),
  ('gujarati', 'Gujarati', 1),
  ('social-science', 'Social Science', 1)
ON DUPLICATE KEY UPDATE
  subject_name = VALUES(subject_name),
  is_enabled = VALUES(is_enabled);
