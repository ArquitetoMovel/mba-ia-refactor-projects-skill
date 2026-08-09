const { AppError } = require('../services/errors');

function sendText(res, statusCode, message) {
    return res.status(statusCode).send(message);
}

function sendJson(res, statusCode, payload) {
    return res.status(statusCode).json(payload);
}

function sendCheckoutSuccess(res, enrollmentId) {
    return sendJson(res, 200, { msg: 'Sucesso', enrollment_id: enrollmentId });
}

function sendError(res, error) {
    if (error instanceof AppError) {
        return sendText(res, error.statusCode, error.message);
    }
    return sendText(res, 500, 'Erro DB');
}

module.exports = {
    sendText,
    sendJson,
    sendCheckoutSuccess,
    sendError,
};
