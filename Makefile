.PHONY: export_requirements

export_requirements:
	cat pyproject.toml | tomlq '.project.dependencies[]' | sed "s/\"//g" > requirements.txt
	cat pyproject.toml | tomlq '.project."optional-dependencies".dev[]' | sed "s/\"//g" > requirements-dev.txt
