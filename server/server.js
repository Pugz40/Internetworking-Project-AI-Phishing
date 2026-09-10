const express = require("express");
const { DatabaseSync } = require("node:sqlite");
const path = require("path");

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, "..")));
const PORT = 3000;
const db = new DatabaseSync("../database/phishing.db");

app.get("/api/test", (req, res) => {
    res.json({ message: "API IS WORKING!" });
});

app.get("/api/email/random", (req, res) => {
    const sources = ["ai", "human"];
    const source = sources[Math.floor(Math.random() * sources.length)];

    if (source === "ai") {
        const email = db.prepare(`
            SELECT * FROM ai_emails
            ORDER BY RANDOM()
            LIMIT 1
        `).get();

        res.json({
            ...email,
            source: "ai"
        });
    } else {
        const email = db.prepare(`
            SELECT * FROM human_emails
            ORDER BY RANDOM()
            LIMIT 1
        `).get();

        res.json({
            ...email,
            source: "human"
        });
    }
});

app.post("/api/session", (req, res) => {
    const result = db.prepare(`
        INSERT INTO quiz_sessions DEFAULT VALUES
    `).run();

    res.json({
        sessionId: result.lastInsertRowid
    });
});

app.post("/api/result", (req, res) => {
    const {
        sessionId,
        emailId,
        emailSource,
        actualLabel,
        userAnswer,
        correct
    } = req.body;

    db.prepare(`
        INSERT INTO user_results
        (session_id, email_id, email_source, actual_label, user_answer, correct)
        VALUES (?, ?, ?, ?, ?, ?)
    `).run(
        sessionId,
        emailId,
        emailSource,
        actualLabel,
        userAnswer,
        correct
    );

    res.json({ message: "Result saved!" });
});

app.listen(PORT, () => {
    console.log(`Server running on http://localhost:${PORT}`);
});