from fastapi.testclient import TestClient
from backend import settings as backend_settings
from backend.main import app

client = TestClient(app)

# activer le mode mock pour tests
backend_settings.settings.pappers_mock_mode = True

print('GET / ->', client.get('/').status_code)
resp = client.get('/dossiers/from-pappers/41816609600069')
print('GET /dossiers/from-pappers ->', resp.status_code)
if resp.status_code == 200:
    print('siret:', resp.json().get('siret'))
    print('siren:', resp.json().get('siren'))
else:
    print('detail:', resp.json())
