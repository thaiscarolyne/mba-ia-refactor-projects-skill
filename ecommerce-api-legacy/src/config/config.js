require('dotenv').config();

function requireEnv(name) {
    const value = process.env[name];
    if (!value) {
        throw new Error(
            `Variável de ambiente obrigatória ausente: ${name}. ` +
            'Copie .env.example para .env e configure os valores.'
        );
    }
    return value;
}

const config = {
    port: parseInt(process.env.PORT || '3000', 10),
    dbUser: process.env.DB_USER || 'admin_master',
    dbPass: requireEnv('DB_PASS'),
    paymentGatewayKey: requireEnv('PAYMENT_GATEWAY_KEY'),
    smtpUser: process.env.SMTP_USER || 'no-reply@example.com',
    adminToken: requireEnv('ADMIN_TOKEN'),
};

module.exports = { config };
