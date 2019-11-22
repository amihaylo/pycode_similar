DOCKER_IMAGE=python:3.7-alpine
PYTHON_FILE=src/pycode_similar_batch.py
TEST_FILE=src/test.py
IN_PATH=./in/sample/*.py
OUT_PATH=./out/output.out
PLAG_LOWERBOUND=0.5

all: run

#Step 1: Thereafter can run this command
run:
	@docker run -it --rm -v $(PWD):/home/work -w /home/work $(DOCKER_IMAGE) python3 $(PYTHON_FILE) $(IN_PATH) -o $(OUT_PATH) -c $(PLAG_LOWERBOUND) -l 4

test:
	@docker run -it --rm -v $(PWD):/home/work -w /home/work $(DOCKER_IMAGE) sh

