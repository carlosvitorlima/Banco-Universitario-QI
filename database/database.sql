CREATE TABLE university (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL
);

CREATE TABLE course (
    id SERIAL PRIMARY KEY,
    name VARCHAR(150) NOT NULL
);

INSERT INTO university (id, name) VALUES (1, 'Universidade QI');
INSERT INTO course (id, name) VALUES (1, 'Engenharia de Software');

CREATE TABLE customer (
    id SERIAL PRIMARY KEY,
    customer_key UUID UNIQUE NOT NULL,
    document VARCHAR(11) UNIQUE NOT NULL,
    university_id INT NOT NULL REFERENCES university(id),
    course_id INT NOT NULL REFERENCES course(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE account_status (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

CREATE TABLE account_type (
    id SERIAL PRIMARY KEY,
    name VARCHAR(50) NOT NULL
);

INSERT INTO account_status (name) VALUES ('ACTIVE'), ('BLOCKED'), ('CLOSED');
INSERT INTO account_type (name) VALUES ('CHECKING'), ('SAVINGS');

CREATE TABLE account (
    id SERIAL PRIMARY KEY,
    account_key UUID UNIQUE NOT NULL,
    customer_id INT NOT NULL REFERENCES customer(id),
    status_id INT NOT NULL REFERENCES account_status(id),
    type_id INT NOT NULL REFERENCES account_type(id),
    balance BIGINT NOT NULL DEFAULT 0,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT check_balance_positive CHECK (balance >= 0)
);

CREATE TABLE account_status_event (
    id SERIAL PRIMARY KEY,
    account_id INT NOT NULL REFERENCES account(id),
    from_status_id INT REFERENCES account_status(id),
    to_status_id INT NOT NULL REFERENCES account_status(id),
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE partner (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL
);

CREATE TABLE benefit (
    id SERIAL PRIMARY KEY,
    benefit_key UUID UNIQUE NOT NULL,
    partner_id INT NOT NULL REFERENCES partner(id),
    title VARCHAR(150) NOT NULL,
    target_university_id INT REFERENCES university(id),
    target_course_id INT REFERENCES course(id)
);

CREATE TABLE benefit_redemption (
    id SERIAL PRIMARY KEY,
    benefit_id INT NOT NULL REFERENCES benefit(id),
    customer_id INT NOT NULL REFERENCES customer(id),
    voucher_code VARCHAR(20) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_customer_benefit_redemption UNIQUE(benefit_id, customer_id)
);

CREATE TABLE insurance (
    id SERIAL PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    monthly_premium INT NOT NULL
);

CREATE TABLE contracted_insurance (
    id SERIAL PRIMARY KEY,
    insurance_id INT NOT NULL REFERENCES insurance(id),
    customer_id INT NOT NULL REFERENCES customer(id),
    policy_number UUID UNIQUE NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW(),
    CONSTRAINT unique_customer_insurance UNIQUE(insurance_id, customer_id)
);

CREATE TABLE transaction (
    id SERIAL PRIMARY KEY,
    transaction_key UUID UNIQUE NOT NULL,
    idempotency_key VARCHAR(100) UNIQUE NOT NULL,
    origin_account_id INT NOT NULL REFERENCES account(id),
    destination_account_id INT NOT NULL REFERENCES account(id),
    amount BIGINT NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE TABLE split_bill (
    id SERIAL PRIMARY KEY,
    transaction_id INT NOT NULL REFERENCES transaction(id),
    payer_account_id INT NOT NULL REFERENCES account(id),
    amount BIGINT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    CONSTRAINT unique_transaction_payer UNIQUE(transaction_id, payer_account_id)
);