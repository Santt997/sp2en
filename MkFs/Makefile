.PHONY: help create delete list update run clean-logs

# =========================
# Config
# =========================

PROJECT_DIR := $(HOME)/Documentos/GitHub/Docs-SrAnderson-mio/learn-quarto/dev/Programs/Utils/4extensionsOfFiles/4ipynbs/sp2en

ENV_NAME := sp2en

YML_FILE := $(PROJECT_DIR)/Envs/sp2en.yml

LOG_DIR := $(HOME)/sp2en_logs


# =========================
# Help
# =========================

help:
	@echo ""
	@echo "sp2en - Micromamba Env Management"
	@echo "========================================="
	@echo ""
	@echo "Commands:"
	@echo "  make create              Create env from yml"
	@echo "  make delete              Delete env"
	@echo "  make list                List installed packages"
	@echo "  make update              Update env"
	@echo "  make run TARGET=/path    Run sp2en.py on target directory"
	@echo "  make clean-logs          Remove logs"
	@echo ""
	@echo "Examples:"
	@echo "  make run TARGET=\$$PWD"
	@echo "  make run TARGET=~/TPs"
	@echo ""


# =========================
# Env
# =========================

create:
	@echo "[CREATE] Creating env: $(ENV_NAME)"

	micromamba create -f $(YML_FILE) -y

	@echo "[OK] Env created"


delete:
	@echo "[DELETE] Removing environment: $(ENV_NAME)"

	micromamba remove -n $(ENV_NAME) --yes

	@echo "[OK] Env removed"


list:
	micromamba list -n $(ENV_NAME)


update:
	@echo "[UPDATE] Updating env: $(ENV_NAME)"

	micromamba update -n $(ENV_NAME) --all --yes

	@echo "[OK] Env updated"


# =========================
# Run
# =========================

TARGET ?= $(PWD)

run:
	@mkdir -p $(LOG_DIR)

	@TIMESTAMP=$$(date +%Y%m%d_%H%M%S); \
	PYTHON_LOG="$(LOG_DIR)/sp2en_python_$$TIMESTAMP.log"; \
	echo "[RUN] sp2en.py"; \
	echo "[TARGET] $(TARGET)"; \
	echo "[LOG] $$PYTHON_LOG"; \
	micromamba run -n $(ENV_NAME) \
		python3 $(PROJECT_DIR)/sp2en.py "$(TARGET)" \
		> "$$PYTHON_LOG" 2>&1; \
	echo "[OK] Completed"


# =========================
# Logs
# =========================

clean-logs:
	@echo "[CLEAN] Removing logs"

	rm -rf $(LOG_DIR)

	@echo "[OK] Logs removed"