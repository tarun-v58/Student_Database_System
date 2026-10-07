CREATE TABLE students (
    id          INTEGER GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name        VARCHAR(100) NOT NULL CHECK (char_length(name) >= 2),
    email       VARCHAR(255) NOT NULL,
    department  VARCHAR(100) NOT NULL,
    age         SMALLINT NOT NULL CHECK (age BETWEEN 15 AND 60),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- One account per email address, ignoring upper/lower case
CREATE UNIQUE INDEX uq_students_email_lower ON students (lower(email));

-- Speeds up filtering by department (used in Phase 15)
CREATE INDEX ix_students_department ON students (department);