# Variables
PYTHON := python3
PIP := pip3
SERVER_FILE := server.py
CLIENT_FILE := client.py

# Targets
all: install run

install:
	$(PIP) install -r requirements.txt

run-server:
	$(PYTHON) $(SERVER_FILE)

run-client:
	$(PYTHON) $(CLIENT_FILE)

clean:
	rm -f *.pyc

.PHONY: all install run-server run-client clean
