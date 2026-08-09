const { withTransaction } = require('../db/database');
const { AppError } = require('./errors');
const { hashPassword } = require('./passwordService');
const { decidePaymentStatus } = require('./paymentGateway');
const userModel = require('../models/userModel');
const courseModel = require('../models/courseModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');
const auditLogModel = require('../models/auditLogModel');

async function checkout(db, input) {
    const name = input.usr;
    const email = input.eml;
    const password = input.pwd;
    const courseId = input.c_id;
    const card = input.card;

    if (!name || !email || !courseId || !card) {
        throw new AppError('Bad Request', 400);
    }

    const course = await courseModel.findActiveCourseById(db, courseId);
    if (!course) {
        throw new AppError('Curso não encontrado', 404);
    }

    const status = decidePaymentStatus(card);
    if (status === 'DENIED') {
        throw new AppError('Pagamento recusado', 400);
    }

    try {
        return await withTransaction(db, async () => {
            let user = await userModel.findUserIdByEmail(db, email);
            let userId;

            if (!user) {
                const passwordHash = hashPassword(password || '123456');
                const created = await userModel.createUser(db, {
                    name,
                    email,
                    passwordHash,
                });
                userId = created.lastID;
            } else {
                userId = user.id;
            }

            const enrollment = await enrollmentModel.createEnrollment(db, {
                userId,
                courseId,
            });
            const enrollmentId = enrollment.lastID;

            await paymentModel.createPayment(db, {
                enrollmentId,
                amount: course.price,
                status,
            });

            await auditLogModel.createAuditLog(
                db,
                `Checkout curso ${courseId} por ${userId}`,
            );

            return { enrollmentId, courseTitle: course.title };
        });
    } catch (error) {
        if (error instanceof AppError) {
            throw error;
        }
        throw new AppError('Erro DB', 500);
    }
}

module.exports = { checkout };
