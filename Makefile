
dependency-graph:
	poetry run pydeps restapiboys --display wsl-open --cluster -o dependencies.svg

cylic-dependencies:
	poetry run pydeps restapiboys --display wsl-open --cluster --show-cycles

debug:
	# TODO: start couchdb from cli.index
	sudo service couchdb status || sudo service couchdb start 
	poetry run restapiboys start --log=debug --port=$$PORT --watch --debug-gunicorn

dev:
	sudo service couchdb status || sudo service couchdb start 
	poetry run restapiboys start --log=info --port=$$PORT --watch

prod:
	sudo service couchdb status || sudo service couchdb start 
	poetry run restapiboys start --log=warn --port=80

test:
	sudo service couchdb status || sudo service couchdb start 
	poetry run pytest -vv

coverage:
	sudo service couchdb status || sudo service couchdb start 
	poetry run pytest -vv --cov=restapiboys
