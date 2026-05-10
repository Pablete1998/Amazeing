PYTHON  = python3
MAIN    = a_maze_ing.py
CONFIG  = config.txt

.PHONY: all install run debug lint lint-strict clean fclean build

all: install

# -- Dependencies -------------------------------------------------------------
install:
	$(PYTHON) -m pip install --upgrade pip
	$(PYTHON) -m pip install flake8 mypy build

# -- Execution ----------------------------------------------------------------
run:
	$(PYTHON) $(MAIN) $(CONFIG)

debug:
	$(PYTHON) -m pdb $(MAIN) $(CONFIG)

# -- Code quality -------------------------------------------------------------
lint:
	flake8 *.py
	mypy *.py \
		--warn-return-any \
		--warn-unused-ignores \
		--ignore-missing-imports \
		--disallow-untyped-defs \
		--check-untyped-defs

lint-strict:
	flake8 *.py
	mypy *.py --strict

# -- mazegen package ----------------------------------------------------------
build:
	$(PYTHON) -m pip install --upgrade build
	cd mazegen_pkg && $(PYTHON) -m build

# -- Cleanup ------------------------------------------------------------------
clean:
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete

fclean: clean
	rm -rf dist/ build/ *.egg-info/
	cd mazegen_pkg && rm -rf dist/ build/ *.egg-info/ 2>/dev/null || true
