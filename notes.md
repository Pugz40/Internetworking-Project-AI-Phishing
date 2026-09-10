# Project Notes

# Database

SQLite database:
database/phishing.db

# Tables

- ai_emails
- human_emails
- quiz_sessions
- user_results

AI emails:
- 2000 total
- 1000 phishing
- 1000 legitimate

Human emails:
- 2000 total
- 1000 phishing
- 1000 legitimate

# API

GET /api/email/random
- Returns a random email
- Randomly chooses between AI and human datasets

POST /api/session
- Creates a new quiz session
- Returns a session ID
- This will be used before we do user logins/etc

POST /api/result
- Saves a user's answer
- Links the answer to a session and email
- Stores whether the answer was correct
- Stores the timestamp

# Current Quiz Flow

START
→ quiz.html
→ create session (if reloaded makes a new session)
→ retrieve random email
→ user selects phishing/legitimate
→ save result
→ retrieve another random email

# Currently Working

- SQLite database
- 4 datasets imported
- Random email API
- Frontend quiz prototype
- Session creation
- Answer/result recording
- Timestamps (COMPLETE)

# Next Steps

- Will explain how the database works in the doc with provided screenshots
- Add number of questions / infographic / finalise structure
- Display results page
- Analyse user performance
- Possibly add user accounts
- Improve UI (Badly)