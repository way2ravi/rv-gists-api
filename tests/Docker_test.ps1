# Move from tests to the project root
Set-Location (Split-Path -Parent $PSScriptRoot)

$env:API_BASE_URL = "http://localhost:8080"
python -m unittest discover -s tests -p "test.py" -v