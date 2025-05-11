.PHONY: run install clean

run:
	python main.py $(ARGS)

run-focused:
	python main.py --path $(PATH) $(ARGS)

load-conversation:
	python main.py --load $(CONV) $(ARGS)

install:
	pip install -r requirements.txt

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
