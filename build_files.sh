echo "BUILD START"

# Install dependencies
python3 -m pip install -r requirements.txt

# Create the output directory if it doesn't exist
mkdir -p staticfiles

# Collect static files
python3 manage.py collectstatic --noinput --clear

echo "BUILD END"