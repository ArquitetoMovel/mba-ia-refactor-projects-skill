const { createCheckoutController } = require('../controllers/checkoutController');
const { createReportController } = require('../controllers/reportController');
const { createUserController } = require('../controllers/userController');

function registerRoutes(app, db) {
    app.post('/api/checkout', createCheckoutController(db));
    app.get('/api/admin/financial-report', createReportController(db));
    app.delete('/api/users/:id', createUserController(db));
}

module.exports = { registerRoutes };
