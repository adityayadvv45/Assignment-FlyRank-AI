require('dotenv').config();
const express = require('express');
const swaggerUi = require('swagger-ui-express');
const swaggerDocument = require('./swagger/openapi.json');

// Instantiating the client here also validates env vars exist before boot.
require('./supabaseClient');

const authRoutes = require('./routes/auth');
const protectedRoutes = require('./routes/protected');
const publicRoutes = require('./routes/public');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(express.json());

app.use('/auth', authRoutes);
app.use('/protected', protectedRoutes);
app.use('/public', publicRoutes);
app.use('/docs', swaggerUi.serve, swaggerUi.setup(swaggerDocument));

app.listen(PORT, () => {
  console.log('Server running and connected to Supabase');
  console.log(`Swagger docs available at http://localhost:${PORT}/docs`);
});
