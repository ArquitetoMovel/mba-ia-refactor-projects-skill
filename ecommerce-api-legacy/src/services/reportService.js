const reportModel = require('../models/reportModel');
const { AppError } = require('./errors');

function buildFinancialReport(rows) {
    const byCourse = new Map();

    for (const row of rows) {
        if (!byCourse.has(row.course_id)) {
            byCourse.set(row.course_id, {
                course: row.course,
                revenue: 0,
                students: [],
            });
        }

        const courseData = byCourse.get(row.course_id);

        if (row.student == null && row.paid == null) {
            continue;
        }

        if (row.payment_status === 'PAID') {
            courseData.revenue += row.paid || 0;
        }

        courseData.students.push({
            student: row.student || 'Unknown',
            paid: row.paid || 0,
        });
    }

    return Array.from(byCourse.values());
}

async function getFinancialReport(db) {
    try {
        const rows = await reportModel.listFinancialReportRows(db);
        return buildFinancialReport(rows);
    } catch (error) {
        throw new AppError('Erro DB', 500);
    }
}

module.exports = { getFinancialReport };
