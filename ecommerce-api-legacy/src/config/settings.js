function readEnv(name, fallback) {
    const value = process.env[name];
    if (value === undefined || value === '') {
        return fallback;
    }
    return value;
}

const settings = {
    port: Number(readEnv('PORT', '3000')),
    dbPath: readEnv('DB_PATH', ':memory:'),
    paymentGatewayKey: readEnv('PAYMENT_GATEWAY_KEY', 'local-dev-only'),
    passwordSalt: readEnv('PASSWORD_SALT', 'local-dev-salt'),
};

module.exports = { settings };
