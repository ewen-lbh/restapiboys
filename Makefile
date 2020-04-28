
dependency-graph:
	poetry run pydeps restapiboys --display wsl-open --cluster -o dependencies.svg

cylic-dependencies:
	poetry run pydeps restapiboys --display wsl-open --cluster --show-cycles

dev:
	poetry run restapiboys start --log debug --watch --port $$PORT

prod:
	poetry run restapiboys start --log warn --port 80

test:
	poetry run pytest -vv
