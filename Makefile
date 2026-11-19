.PHONY: test demo audit sarif snapshot check clean

PYTHON ?= python3
DEMO := --root examples/demo

test:
	$(PYTHON) -m unittest discover -s tests -v

demo:
	$(PYTHON) -m prism $(DEMO) resolve src/app.py --why --no-color

audit:
	$(PYTHON) -m prism $(DEMO) audit src/app.py --no-color

sarif:
	$(PYTHON) -m prism $(DEMO) audit src/app.py --format sarif > prism.sarif

snapshot:
	$(PYTHON) -m prism $(DEMO) snapshot

check:
	$(PYTHON) -m prism $(DEMO) check

clean:
	rm -rf build dist *.egg-info prism.sarif .pytest_cache
	find . -type d -name __pycache__ -prune -exec rm -rf {} +
