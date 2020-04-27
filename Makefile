
dependency-graph:
	poetry run pydeps restapiboys --display wsl-open --cluster -o dependencies.svg

cylic-dependencies:
	poetry run pydeps restapiboys --display wsl-open --cluster --show-cycles

dev:
	poetry run restapiboys start --log debug --watch

prod:
	poetry run restapiboys start --log warn
