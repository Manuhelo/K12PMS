echo "BUILD START"

# Install dependencies
python3.8 -m pip install -r requirements.txt

# Create the output directory if it doesn't exist
mkdir -p staticfiles_build

# Collect static files
python3.8 manage.py collectstatic --noinput --clear

echo "BUILD END"