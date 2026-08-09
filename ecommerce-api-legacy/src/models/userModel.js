const { get, run } = require('../db/database');

function findUserIdByEmail(db, email) {
    return get(db, 'SELECT id FROM users WHERE email = ?', [email]);
}

function createUser(db, { name, email, passwordHash }) {
    return run(db, 'INSERT INTO users (name, email, pass) VALUES (?, ?, ?)', [
        name,
        email,
        passwordHash,
    ]);
}

function deleteUserById(db, id) {
    return run(db, 'DELETE FROM users WHERE id = ?', [id]);
}

module.exports = {
    findUserIdByEmail,
    createUser,
    deleteUserById,
};
