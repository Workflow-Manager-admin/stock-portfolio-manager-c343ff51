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

Production order placement and portfolio actions require integration with Zerodha Kite's REST API.

- User-specific access and refresh tokens for Kite REST API (must be securely stored + managed, e.g., in your DB).
- The following global credentials must be set in `.env` for backend startup:

```
KITE_API_KEY=d9hqdwpwqs1fpn9v
KITE_API_SECRET=zutgh8i03uanjfa16p1ef5hd9a8ne69g
```
Alternatively, the legacy environment keys are also read if present:
```
ZERODHA_KITE_API_KEY=d9hqdwpwqs1fpn9v
ZERODHA_KITE_API_SECRET=zutgh8i03uanjfa16p1ef5hd9a8ne69g
```
**IMPORTANT:** Never commit secrets to public repos. Store secret values in environment variables only.

- Users must OAuth authenticate via `/kite/oauth-url` → redirect to browser, sign in and approve
- The backend exchanges the `request_token` for an `access_token` using `/kite/generate-token`
- Place orders using `/order` with a valid user's access_token
- For API details, see `src/api/kite_service.py`, and FastAPI docs

Demo code scaffolds endpoints for interactive authentication and order placement. Production integration should also persist/refresh tokens securely and manage user identities.
