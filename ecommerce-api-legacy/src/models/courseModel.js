const { get } = require('../db/database');

function findActiveCourseById(db, courseId) {
    return get(db, 'SELECT * FROM courses WHERE id = ? AND active = 1', [courseId]);
}

module.exports = { findActiveCourseById };
