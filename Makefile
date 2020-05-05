

dependency-graph:
	poetry run pydeps restapiboys --display wsl-open --cluster -o dependencies.svg

cylic-dependencies:
	poetry run pydeps restapiboys --display wsl-open --cluster --show-cycles

debug:
	# TODO: start couchdb from cli.index
	poetry run restapiboys start --log=debug --port=$$PORT --watch --debug-gunicorn

dev:
	poetry run restapiboys start --log=info --port=$$PORT --watch

prod:
	poetry run restapiboys start --log=warn --port=80

test:
	# Starting service CouchDB
	poetry run python -c "from initsystem import Service;c=Service('couchdb');c.start()"
	poetry run pytest -vv
	# Stopping service CouchDB
	poetry run python -c "from initsystem import Service;c=Service('couchdb');c.stop()"

coverage:
	# Starting service CouchDB
	poetry run python -c "from initsystem import Service;c=Service('couchdb');c.start()"
	poetry run pytest -vv --cov=restapiboys
	# Stopping service CouchDB
	poetry run python -c "from initsystem import Service;c=Service('couchdb');c.stop()"
