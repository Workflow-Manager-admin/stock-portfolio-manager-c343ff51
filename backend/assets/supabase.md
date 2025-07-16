# Supabase Integration for Stock Portfolio Manager

This backend uses Supabase for user authentication (registration, login, session management). The required environment variables in your `.env` are:

- `SUPABASE_URL`: The REST API URL of your Supabase instance.
- `SUPABASE_KEY`: Your Supabase service API key (should be `anon` or service role for backend).

The authentication endpoints `/auth/register` and `/auth/login` connect directly to Supabase Auth endpoints via REST. User JWTs are issued by Supabase and checked on each protected endpoint by calling the `/auth/v1/user` endpoint. The token must be included in the `Authorization: Bearer <token>` header.

To persist user portfolio data and manage advanced analytics, you can use Supabase PostgreSQL via REST or client library (future expansion, not fully shown in this demo implementation).

## Requirements

```
SUPABASE_URL=https://<your-project>.supabase.co
SUPABASE_KEY=<your-service-api-key>
```

---

# Zerodha Kite API Integration

Production order placement requires:

- User-specific access and refresh tokens for Kite REST API (must be securely stored + managed).
- Global credentials in `.env`:
  - `ZERODHA_KITE_API_KEY`
  - `ZERODHA_KITE_API_SECRET`

Demo code provides endpoint scaffolding and simulated responses. Production integration would use (1) user OAuth flow, (2) kiteconnect python client, etc.

---
