const checkoutService = require('../services/checkoutService');
const { sendCheckoutSuccess, sendError } = require('../views/httpResponses');

function createCheckoutController(db) {
    return async function checkout(req, res) {
        try {
            const result = await checkoutService.checkout(db, req.body || {});
            return sendCheckoutSuccess(res, result.enrollmentId);
        } catch (error) {
            return sendError(res, error);
        }
    };
}

module.exports = { createCheckoutController };
