CREATE TABLE IF NOT EXISTS employee
(
    id SERIAL PRIMARY KEY,
    name character varying,
    birthday date,
    birth_place character varying,
    nik bigint,
    position character varying,
    date_hired date,
    created_at timestamp without time zone
)

CREATE TABLE IF NOT EXISTS users
(
    id SERIAL PRIMARY KEY,
    email character varying NOT NULL,
    username character varying NOT NULL,
    password character varying NOT NULL,
    role character varying
)