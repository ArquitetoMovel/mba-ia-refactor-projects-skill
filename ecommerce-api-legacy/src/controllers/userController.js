const userService = require('../services/userService');
const { sendText, sendError } = require('../views/httpResponses');

function createUserController(db) {
    return async function deleteUser(req, res) {
        try {
            await userService.deleteUser(db, req.params.id);
            return sendText(res, 200, 'Usuário deletado.');
        } catch (error) {
            return sendError(res, error);
        }
    };
}

module.exports = { createUserController };
