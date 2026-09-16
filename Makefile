.PHONY: up up-d down logs ps test-e2e worktree

up:
	docker compose up --build

up-d:
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

ps:
	docker compose ps

test-e2e:
	cd tests/e2e && npx playwright test

# Usage: make worktree NAME=symptom-ui BRANCH=feat/symptom-intake-ui
worktree:
	git worktree add ../Client-Project-wt-$(NAME) -b $(BRANCH)
