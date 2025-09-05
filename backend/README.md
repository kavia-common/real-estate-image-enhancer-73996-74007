# Real Estate Image Enhancer - Backend

FastAPI backend providing:
- Authentication (register/login via JWT)
- Image upload (batch), metadata storage
- Natural language edit requests and history
- Usage/trial tracking
- Subscription management and Stripe (stubbed) checkout + webhook
- Dashboard aggregated APIs

Run:
- pip install -r requirements.txt
- Configure environment via .env (see .env.example)
- uvicorn src.api.main:app --reload

OpenAPI:
- Generate: python -m src.api.generate_openapi
- Output: interfaces/openapi.json
