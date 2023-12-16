venvname="env92"

if [ ! -d "$venvname" ]; then
    python -m venv "$venvname"
fi

source "$venvname/bin/activate"
pip install -r requirements.txt

echo "this is working dir92 : $PWD"
python manage.py makemigrations
python manage.py migrate
python manage.py runserver 0.0.0.0:9200
