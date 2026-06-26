const express = require('express');
const CheckoutController = require('../controllers/CheckoutController');

const router = express.Router();
router.post('/api/checkout', CheckoutController.checkout);

module.exports = router;
