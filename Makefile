.PHONY: help install install-wrapper install-wrapper-user uninstall-wrapper clean

SCRIPT_DIR = $(shell pwd)

help:
	@echo "=== semacro ==="
	@echo ""
	@echo "Setup:"
	@echo "  install              - Install wrapper (interactive: /usr/local/bin or ~/bin)"
	@echo "  install-wrapper-user - Install wrapper to ~/bin (non-interactive)"
	@echo "  uninstall-wrapper    - Remove wrapper scripts"
	@echo "  clean                - Remove generated files"

install: install-wrapper

install-wrapper:
	@echo "Installing semacro wrapper..."
	@echo ""
	@echo "Choose installation location:"
	@echo "  1) /usr/local/bin (requires sudo, available system-wide)"
	@echo "  2) ~/bin (no sudo, user-only)"
	@echo ""
	@read -p "Enter choice [1/2]: " choice; \
	if [ "$$choice" = "1" ]; then \
		echo "Installing to /usr/local/bin..."; \
		echo '#!/bin/bash' | sudo tee /usr/local/bin/semacro > /dev/null; \
		echo 'exec python3 $(SCRIPT_DIR)/semacro.py "$$@"' | sudo tee -a /usr/local/bin/semacro > /dev/null; \
		sudo chmod +x /usr/local/bin/semacro; \
		echo "Wrapper installed to /usr/local/bin"; \
	elif [ "$$choice" = "2" ]; then \
		echo "Installing to ~/bin..."; \
		mkdir -p ~/bin; \
		echo '#!/bin/bash' > ~/bin/semacro; \
		echo 'exec python3 $(SCRIPT_DIR)/semacro.py "$$@"' >> ~/bin/semacro; \
		chmod +x ~/bin/semacro; \
		echo "Wrapper installed to ~/bin"; \
		if ! echo $$PATH | grep -q "$$HOME/bin"; then \
			echo ""; \
			echo "~/bin is not in your PATH. Add to ~/.bashrc:"; \
			echo "  export PATH=\"\$$HOME/bin:\$$PATH\""; \
			echo "Then run: source ~/.bashrc"; \
		fi; \
	else \
		echo "Invalid choice. Installation cancelled."; \
		exit 1; \
	fi
	@echo ""
	@echo "If the default include path doesn't work, add to ~/.bashrc:"
	@echo "  export SEMACRO_INCLUDE_PATH=/path/to/policy/include"

install-wrapper-user:
	@echo "Installing semacro wrapper to ~/bin..."
	@mkdir -p ~/bin
	@echo '#!/bin/bash' > ~/bin/semacro
	@echo 'exec python3 $(SCRIPT_DIR)/semacro.py "$$@"' >> ~/bin/semacro
	@chmod +x ~/bin/semacro
	@echo "Wrapper installed to ~/bin"
	@if ! echo $$PATH | grep -q "$$HOME/bin"; then \
		echo ""; \
		echo "~/bin is not in your PATH. Add to ~/.bashrc:"; \
		echo "  export PATH=\"\$$HOME/bin:\$$PATH\""; \
		echo "Then run: source ~/.bashrc"; \
	fi
	@echo ""
	@echo "If the default include path doesn't work, add to ~/.bashrc:"
	@echo "  export SEMACRO_INCLUDE_PATH=/path/to/policy/include"

uninstall-wrapper:
	@echo "Removing semacro wrapper..."
	@sudo rm -f /usr/local/bin/semacro 2>/dev/null || echo "  (skipped /usr/local/bin - no sudo access or not found)"
	@rm -f ~/bin/semacro 2>/dev/null || echo "  (~/bin/semacro not found)"
	@echo "Wrapper removal complete"

clean:
	@rm -rf __pycache__ *.pyc
	@echo "Cleaned"
