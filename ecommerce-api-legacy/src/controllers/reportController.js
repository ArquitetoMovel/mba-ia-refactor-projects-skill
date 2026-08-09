const reportService = require('../services/reportService');
const { sendJson, sendError } = require('../views/httpResponses');

function createReportController(db) {
    return async function financialReport(req, res) {
        try {
            const report = await reportService.getFinancialReport(db);
            return sendJson(res, 200, report);
        } catch (error) {
            return sendError(res, error);
        }
    };
}

module.exports = { createReportController };
