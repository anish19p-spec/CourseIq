CREATE EXTENSION IF NOT EXISTS pgcrypto;

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    major TEXT NOT NULL,
    year_in_school TEXT NOT NULL,
    gpa NUMERIC(3, 2) NOT NULL CHECK (gpa >= 0 AND gpa <= 4),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS courses (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    department_code TEXT NOT NULL,
    course_number TEXT NOT NULL,
    name TEXT NOT NULL,
    CONSTRAINT courses_department_number_unique UNIQUE (department_code, course_number)
);

CREATE TABLE IF NOT EXISTS syllabi (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    course_id UUID NOT NULL REFERENCES courses (id) ON DELETE CASCADE,
    professor_name TEXT NOT NULL,
    term TEXT NOT NULL,
    raw_llm_json JSONB NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS student_histories (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users (id) ON DELETE CASCADE,
    course_id UUID NOT NULL REFERENCES courses (id) ON DELETE CASCADE,
    reported_comfort_level INT NOT NULL CHECK (reported_comfort_level BETWEEN 1 AND 10),
    actual_grade TEXT NOT NULL,
    actual_hours_spent NUMERIC(8, 2) NOT NULL CHECK (actual_hours_spent >= 0),
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_syllabi_course_id ON syllabi (course_id);
CREATE INDEX IF NOT EXISTS idx_student_histories_user_id ON student_histories (user_id);
CREATE INDEX IF NOT EXISTS idx_student_histories_course_id ON student_histories (course_id);
