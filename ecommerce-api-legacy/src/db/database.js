const sqlite3 = require('sqlite3').verbose();
const { settings } = require('../config/settings');

function openDatabase(dbPath = settings.dbPath) {
    return new sqlite3.Database(dbPath);
}

function run(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.run(sql, params, function onRun(err) {
            if (err) {
                reject(err);
                return;
            }
            resolve({ lastID: this.lastID, changes: this.changes });
        });
    });
}

function get(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.get(sql, params, (err, row) => {
            if (err) {
                reject(err);
                return;
            }
            resolve(row);
        });
    });
}

function all(db, sql, params = []) {
    return new Promise((resolve, reject) => {
        db.all(sql, params, (err, rows) => {
            if (err) {
                reject(err);
                return;
            }
            resolve(rows);
        });
    });
}

async function withTransaction(db, work) {
    await run(db, 'BEGIN');
    try {
        const result = await work();
        await run(db, 'COMMIT');
        return result;
    } catch (error) {
        try {
            await run(db, 'ROLLBACK');
        } catch (rollbackError) {
            error.rollbackError = rollbackError;
        }
        throw error;
    }
}

async function initSchemaAndSeed(db) {
    await run(db, 'CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT, pass TEXT)');
    await run(
        db,
        'CREATE TABLE courses (id INTEGER PRIMARY KEY, title TEXT, price REAL, active INTEGER)',
    );
    await run(
        db,
        'CREATE TABLE enrollments (id INTEGER PRIMARY KEY, user_id INTEGER, course_id INTEGER)',
    );
    await run(
        db,
        'CREATE TABLE payments (id INTEGER PRIMARY KEY, enrollment_id INTEGER, amount REAL, status TEXT)',
    );
    await run(
        db,
        'CREATE TABLE audit_logs (id INTEGER PRIMARY KEY, action TEXT, created_at DATETIME)',
    );

    await run(
        db,
        "INSERT INTO users (name, email, pass) VALUES ('Leonan', 'leonan@fullcycle.com.br', '123')",
    );
    await run(
        db,
        "INSERT INTO courses (title, price, active) VALUES ('Clean Architecture', 997.00, 1), ('Docker', 497.00, 1)",
    );
    await run(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (1, 1)');
    await run(
        db,
        "INSERT INTO payments (enrollment_id, amount, status) VALUES (1, 997.00, 'PAID')",
    );
}

module.exports = {
    openDatabase,
    run,
    get,
    all,
    withTransaction,
    initSchemaAndSeed,
};
