const CourseModel = require('../models/CourseModel');
const UserModel = require('../models/UserModel');
const EnrollmentModel = require('../models/EnrollmentModel');
const PaymentModel = require('../models/PaymentModel');
const { dbRun } = require('../database/db');
const { config } = require('../config/config');

const localCache = new Map();

class CheckoutController {
    static async checkout(req, res) {
        const username = req.body.usr || req.body.name;
        const email = req.body.eml || req.body.email;
        const password = req.body.pwd || req.body.password;
        const courseId = req.body.c_id || req.body.courseId;
        const creditCard = req.body.card || req.body.cardNumber;

        if (!username || !email || !courseId || !creditCard) {
            return res.status(400).json({ erro: "Bad Request. Campos obrigatórios ausentes." });
        }

        try {
            const course = await CourseModel.getByIdAndActive(courseId);
            if (!course) {
                return res.status(404).json({ erro: "Curso não encontrado ou inativo." });
            }

            let user = await UserModel.getByEmail(email);
            
            await dbRun("BEGIN TRANSACTION");
            
            try {
                let userId;
                if (!user) {
                    const plainPass = password || "123456";
                    userId = await UserModel.create(username, email, plainPass);
                } else {
                    userId = user.id;
                }

                const maskedCard = creditCard.length > 4 ? `****-****-****-${creditCard.substring(creditCard.length - 4)}` : "****";
                console.log(`[PAYMENT] Processando cartão ${maskedCard}`);
                
                const status = creditCard.toString().startsWith("4") ? "PAID" : "DENIED";
                if (status === "DENIED") {
                    await dbRun("ROLLBACK");
                    return res.status(400).json({ erro: "Pagamento recusado" });
                }

                const enrollmentId = await EnrollmentModel.create(userId, courseId);
                await PaymentModel.create(enrollmentId, course.price, status);
                await dbRun("INSERT INTO audit_logs (action, created_at) VALUES (?, datetime('now'))", [
                    `Checkout curso ${courseId} por usuario_id ${userId}`
                ]);

                await dbRun("COMMIT");

                localCache.set(`last_checkout_${userId}`, course.title);
                console.log(`[CACHE] Salvando no cache: last_checkout_${userId} -> ${course.title}`);

                return res.status(200).json({ msg: "Sucesso", enrollment_id: enrollmentId });
            } catch (err) {
                await dbRun("ROLLBACK");
                throw err;
            }
        } catch (err) {
            console.error("Erro no fluxo de checkout:", err);
            return res.status(500).json({ erro: "Erro interno no servidor durante o checkout." });
        }
    }
}

module.exports = CheckoutController;
