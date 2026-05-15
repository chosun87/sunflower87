# sunflower87

Personal Financial Dashboard Monorepo.

## Project Structure

- `be/`: FastAPI Backend
- `fe/`: React/PrimeReact Frontend

## Security

- API keys and environment variables are managed via `.env` files.
- `.env` files and environment-specific folders (venv, node_modules) are excluded from version control.

## Development

### Backend (be)
```bash
cd be
python -m venv venv
# Activate venv
pip install -r requirements.txt
python main.py
```

### Frontend (fe)
```bash
cd fe
npm install
npm run dev
```

## Branching Strategy

- `main`: Production-ready code. No direct pushes.
- `feature/*`: New features and setup. Merge via Pull Request.
