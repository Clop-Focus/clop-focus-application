SHELL := /bin/bash
APP_MODULE ?= app_lazy:app
PORT ?= 8000

.PHONY: run stop logs health restart

run:
	@if [[ "$$PWD" == *"gaze-backend" ]]; then \
		source .venv/bin/activate && \
		lsof -ti :$(PORT) | xargs -r kill -9 || true && \
		nohup uvicorn $(APP_MODULE) --host 0.0.0.0 --port $(PORT) --log-level info > server.log 2>&1 & \
		echo $$! > uvicorn.pid && echo "PID $$(cat uvicorn.pid)"; \
	else \
		cd gaze-backend && source .venv/bin/activate && \
		lsof -ti :$(PORT) | xargs -r kill -9 || true && \
		nohup uvicorn $(APP_MODULE) --host 0.0.0.0 --port $(PORT) --log-level info > server.log 2>&1 & \
		echo $$! > uvicorn.pid && echo "PID $$(cat uvicorn.pid)"; \
	fi

health:
	curl -sS http://localhost:$(PORT)/health || true

logs:
	@if [[ "$$PWD" == *"gaze-backend" ]]; then \
		tail -f server.log; \
	else \
		cd gaze-backend && tail -f server.log; \
	fi

stop:
	@if [[ "$$PWD" == *"gaze-backend" ]]; then \
		if [[ -f uvicorn.pid ]]; then \
			kill -TERM $$(cat uvicorn.pid) 2>/dev/null || true; rm -f uvicorn.pid; echo "Parado."; \
		else echo "Sem PID."; fi; \
	else \
		cd gaze-backend && if [[ -f uvicorn.pid ]]; then \
			kill -TERM $$(cat uvicorn.pid) 2>/dev/null || true; rm -f uvicorn.pid; echo "Parado."; \
		else echo "Sem PID."; fi; \
	fi

restart: stop run
