.PHONY: dev test eval eval-heldout ablate chaos calibrate seed demo
PYTHON ?= python
dev:
	$(PYTHON) -m uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
test:
	$(PYTHON) -m unittest discover -s tests -v
eval:
	$(PYTHON) -m evals.runner --split dev
eval-heldout:
	$(PYTHON) -m evals.runner --split heldout --heldout --confirm
ablate:
	$(PYTHON) -m evals.ablations
chaos:
	$(PYTHON) -m evals.chaos
calibrate:
	$(PYTHON) -m evals.calibrate
seed:
	$(PYTHON) -m ontology.build_taxonomy
	$(PYTHON) -m evals.generate_data
demo:
	$(PYTHON) -m agent.main demo
