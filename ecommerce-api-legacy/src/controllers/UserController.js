const UserModel = require('../models/UserModel');

class UserController {
    static async deleteUser(req, res) {
        const id = req.params.id;
        try {
            const user = await UserModel.getById(id);
            if (!user) {
                return res.status(404).json({ erro: "Usuário não encontrado." });
            }
            await UserModel.delete(id);
            return res.status(200).json({
                mensagem: "Usuário deletado, mas as matrículas e pagamentos foram limpos/desassociados no banco."
            });
        } catch (err) {
            console.error("Erro ao deletar usuário:", err);
            return res.status(500).json({ erro: "Erro interno no servidor ao deletar usuário." });
        }
    }
}

module.exports = UserController;
