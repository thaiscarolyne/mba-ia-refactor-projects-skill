const { dbGet, dbAll } = require('../database/db');

class CourseModel {
    static async getByIdAndActive(id) {
        return await dbGet("SELECT * FROM courses WHERE id = ? AND active = 1", [id]);
    }

    static async getAll() {
        return await dbAll("SELECT * FROM courses");
    }
}

module.exports = CourseModel;
