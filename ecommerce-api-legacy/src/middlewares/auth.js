const { config } = require('../config/config');

const adminRequired = (req, res, next) => {
    const authHeader = req.headers.authorization || "";
    const token = authHeader.replace("Bearer ", "").trim();

    if (!token || token !== config.adminToken) {
        return res.status(401).json({ erro: "Não autorizado. Token de administrador inválido ou ausente." });
    }
    next();
};

module.exports = { adminRequired };
