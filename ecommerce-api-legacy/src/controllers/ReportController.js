const { dbAll } = require('../database/db');

class ReportController {
    static async getFinancialReport(req, res) {
        try {
            const query = `
                SELECT c.id as course_id, c.title as course_title,
                       u.name as student_name,
                       p.amount as payment_amount, p.status as payment_status
                FROM courses c
                LEFT JOIN enrollments e ON c.id = e.course_id
                LEFT JOIN users u ON e.user_id = u.id
                LEFT JOIN payments p ON e.id = p.enrollment_id
            `;
            
            const rows = await dbAll(query);
            const reportMap = new Map();
            
            for (const row of rows) {
                const cid = row.course_id;
                if (!reportMap.has(cid)) {
                    reportMap.set(cid, {
                        course: row.course_title,
                        revenue: 0,
                        students: []
                    });
                }
                
                const courseData = reportMap.get(cid);
                
                if (row.student_name) {
                    const paidAmount = (row.payment_status === 'PAID') ? row.payment_amount : 0;
                    if (row.payment_status === 'PAID') {
                        courseData.revenue += row.payment_amount;
                    }
                    courseData.students.push({
                        student: row.student_name,
                        paid: paidAmount
                    });
                }
            }
            
            const report = Array.from(reportMap.values());
            return res.status(200).json(report);
        } catch (err) {
            console.error("Erro ao gerar relatório financeiro:", err);
            return res.status(500).json({ erro: "Erro interno no servidor ao carregar relatório." });
        }
    }
}

module.exports = ReportController;
