# Makefile ;)

dist: clean
	@pip3 install --upgrade build twine
	python -m build
	twine check dist/*

push:
	twine upload dist/*

all: dist push

clean:
	find . -type f -name *.pyc -delete
	find . -type d -name __pycache__ -delete
	rm -rf build
	rm -rf dist
	rm -rf sonnenbatterie/*.egg-info
	rm -rf sonnenbatterie2/*.egg-info
	rm -rf timeofuse/*.egg-info

.phony: dist
