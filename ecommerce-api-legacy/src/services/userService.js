const { withTransaction } = require('../db/database');
const { AppError } = require('./errors');
const userModel = require('../models/userModel');
const enrollmentModel = require('../models/enrollmentModel');
const paymentModel = require('../models/paymentModel');

async function deleteUser(db, userId) {
    try {
        await withTransaction(db, async () => {
            await paymentModel.deletePaymentsByUserId(db, userId);
            await enrollmentModel.deleteEnrollmentsByUserId(db, userId);
            const result = await userModel.deleteUserById(db, userId);
            if (result.changes === 0) {
                throw new AppError('Usuário não encontrado', 404);
            }
        });
    } catch (error) {
        if (error instanceof AppError) {
            throw error;
        }
        throw new AppError('Erro DB', 500);
    }
}

module.exports = { deleteUser };
