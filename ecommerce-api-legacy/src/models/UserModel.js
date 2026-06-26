const { dbGet, dbRun, dbAll } = require('../database/db');
const bcrypt = require('bcryptjs');

class UserModel {
    static async getByEmail(email) {
        return await dbGet("SELECT * FROM users WHERE email = ?", [email]);
    }

    static async getById(id) {
        return await dbGet("SELECT id, name, email FROM users WHERE id = ?", [id]);
    }

    static async create(name, email, plainPassword) {
        const hash = bcrypt.hashSync(plainPassword, 10);
        const result = await dbRun("INSERT INTO users (name, email, pass) VALUES (?, ?, ?)", [name, email, hash]);
        return result.lastID;
    }

    static async delete(id) {
        return await dbRun("DELETE FROM users WHERE id = ?", [id]);
    }
    
    static async getAll() {
        return await dbAll("SELECT id, name, email FROM users");
    }
}

module.exports = UserModel;
