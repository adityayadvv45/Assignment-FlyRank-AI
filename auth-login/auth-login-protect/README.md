# Auth Login & Protect

A secure REST API built with Node.js, Express, and Supabase Auth. It handles sign up, log in,
log out, and protects routes with JWT verification via reusable middleware.

## Setup

1. Create a free project at supabase.com and grab your **Project URL** and **anon key**
   from Project Settings → API.
2. Copy `.env.example` to `.env` and fill in your values:
   ```
   SUPABASE_URL=your_project_url
   SUPABASE_KEY=your_anon_key
   PORT=3000
   ```
3. Install dependencies:
   ```
   npm install
   ```

## Run

```
npm start
```

You should see `Server running and connected to Supabase` in the terminal.
Swagger docs are available at `http://localhost:3000/docs`.

## API Reference

| Method | Route                 | Auth required | Description                    |
|--------|------------------------|:--------------:|---------------------------------|
| POST   | /auth/signup           | No             | Create a new user account      |
| POST   | /auth/login            | No             | Log in, returns JWT + refresh  |
| POST   | /auth/logout           | Yes (Bearer)   | Ends the session                |
| GET    | /protected/profile     | Yes (Bearer)   | Returns the caller's profile   |
| GET    | /protected/dashboard   | Yes (Bearer)   | Sample second protected route  |
| GET    | /public/info           | No             | Public unprotected message     |

## Swagger UI

Open `/docs`, click **Authorize**, paste your access token (no need to type "Bearer "),
then try `/protected/profile` directly from the browser.

![Swagger UI screenshot](./swagger-screenshot.png)

## Notes

- `.env` is git-ignored — never commit real Supabase keys.
- Auth verification logic lives in `middleware/authMiddleware.js` and is reused across
  every protected route.
