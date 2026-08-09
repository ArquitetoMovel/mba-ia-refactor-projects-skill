const { run } = require('../db/database');

function createPayment(db, { enrollmentId, amount, status }) {
    return run(
        db,
        'INSERT INTO payments (enrollment_id, amount, status) VALUES (?, ?, ?)',
        [enrollmentId, amount, status],
    );
}

function deletePaymentsByUserId(db, userId) {
    return run(
        db,
        `DELETE FROM payments
         WHERE enrollment_id IN (
           SELECT id FROM enrollments WHERE user_id = ?
         )`,
        [userId],
    );
}

module.exports = {
    createPayment,
    deletePaymentsByUserId,
};
