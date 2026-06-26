const express = require('express');
const ReportController = require('../controllers/ReportController');
const { adminRequired } = require('../middlewares/auth');

const router = express.Router();
router.get('/api/admin/financial-report', adminRequired, ReportController.getFinancialReport);

module.exports = router;
