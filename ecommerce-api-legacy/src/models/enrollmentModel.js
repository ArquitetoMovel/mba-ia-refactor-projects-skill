const { run } = require('../db/database');

function createEnrollment(db, { userId, courseId }) {
    return run(db, 'INSERT INTO enrollments (user_id, course_id) VALUES (?, ?)', [
        userId,
        courseId,
    ]);
}

function deleteEnrollmentsByUserId(db, userId) {
    return run(db, 'DELETE FROM enrollments WHERE user_id = ?', [userId]);
}

module.exports = {
    createEnrollment,
    deleteEnrollmentsByUserId,
};
