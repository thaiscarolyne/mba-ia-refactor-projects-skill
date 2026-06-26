const express = require('express');
const { config } = require('./config/config');
const { initDb } = require('./database/db');

const checkoutRoutes = require('./routes/checkoutRoutes');
const reportRoutes = require('./routes/reportRoutes');
const userRoutes = require('./routes/userRoutes');

const app = express();
app.use(express.json());

app.use(checkoutRoutes);
app.use(reportRoutes);
app.use(userRoutes);

app.get('/', (req, res) => {
    res.json({
        message: "Frankenstein LMS API (Refatorada para MVC)",
        version: "1.1.0"
    });
});

initDb().then(() => {
    app.listen(config.port, () => {
        console.log(`Frankenstein LMS rodando na porta ${config.port}...`);
    });
}).catch(err => {
    console.error("Falha ao inicializar o banco de dados:", err);
    process.exit(1);
});
