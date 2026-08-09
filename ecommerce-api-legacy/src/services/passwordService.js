const crypto = require('crypto');
const { settings } = require('../config/settings');

function hashPassword(password) {
    return crypto
        .scryptSync(String(password), settings.passwordSalt, 32)
        .toString('hex');
}

module.exports = { hashPassword };
