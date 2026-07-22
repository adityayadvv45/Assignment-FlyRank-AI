const express = require('express');
const router = express.Router();
const requireAuth = require('../middleware/authMiddleware');

// GET /protected/profile
router.get('/profile', requireAuth, (req, res) => {
  const { id, email, created_at } = req.user;
  return res.status(200).json({ id, email, created_at });
});

// GET /protected/dashboard — second protected route for the Stage 4 checkpoint
router.get('/dashboard', requireAuth, (req, res) => {
  return res.status(200).json({
    message: `Welcome to your dashboard, ${req.user.email}!`
  });
});

module.exports = router;
