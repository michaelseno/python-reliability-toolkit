INVALID_LOGIN_CASES = [
    ("invalid@example.com", "wrongpass"),
    ("nobody@example.com", "Password123!"),
    ("admin@example.com", "badpass"),
    ("test@example.com", "123456"),
    ("foo@bar.com", "incorrect"),
]

FORGOT_EMAIL_CASES = [
    "a@example.com",
    "does-not-exist@example.net",
    "foo@bar.invalid",
    "nobody@toolshop.dev",
    "edgecase+rk@example.com",
]
