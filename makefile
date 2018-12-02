DOCKER_IMAGE=pycode_similar
PYTHON_FILE=src/pycode_similar_batch.py
TEST_FILE=src/test.py
IN_PATH=./in/sample/*.py
# IN_PATH=./in/assig2-all/*.py
OUT_PATH=./out/output.out
PLAG_LOWERBOUND=0.5

all: run

#Step 1. Run this once
build:
	docker build -t $(DOCKER_IMAGE) .

#Step 2: Thereafter can run this command
run:
	@docker run -it --rm -v $(PWD):/home/work -w /home/work $(DOCKER_IMAGE) python3 $(PYTHON_FILE) $(IN_PATH) -o $(OUT_PATH) -c $(PLAG_LOWERBOUND) -l 4 -d

test:
	@docker run -it --rm -v $(PWD):/home/work -w /home/work $(DOCKER_IMAGE) sh

