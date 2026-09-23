@../AGENTS.md

## backend-specific conventions

- **Stack**: Java 21, Spring Boot 4.1.1, Maven. Use the system `mvn` — the generated `mvnw`
  wrapper tries to download its own Maven distribution and may fail without direct internet
  access to `repo.maven.apache.org`; prefer `mvn` directly in this environment.
- **Run**: `mvn spring-boot:run`. **Build/verify**: `mvn -q compile` or `mvn -q verify`.
  **All Maven commands here run from `backend/`, not the repo root** — there's no root
  `pom.xml`, so running them one level up fails with `No plugin found for prefix
  'spring-boot'` (or `there is no POM in this directory`), which reads like a broken setup
  but just means the wrong working directory.
- **Tests**: JUnit under `src/test/java`, mirroring the package under test. `mvn -q test`
  runs them (`mvn -q verify` runs tests as part of the build). **No database needed** —
  the backend is stateless as of `docs/specs/remove-databases.md`, so
  `BackendApplicationTests` boots the full context without one and CI needs no service
  container.
- **No persistence layer**: no JPA, no Flyway, no datasource. The backend validates a
  request, calls `ml-service`, and returns the result. Nothing is stored. If persistence
  comes back, it comes back with something that reads it — the last one had two writes and
  zero reads.
- **Correlation ID**: handled by `config/CorrelationIdFilter.java` — reads/generates
  `X-Correlation-Id`, puts it in the SLF4J MDC (`correlationId` key) so it's in every log line
  automatically (see the `logging.pattern.console` in `application.yml`).
- **Errors**: throw exceptions and let `config/GlobalExceptionHandler.java` map them to the
  shared `ApiError` shape (`code`/`message`/`details`) — see docs/API_CONTRACTS.md. Add
  specific `@ExceptionHandler` cases there as new error types appear; don't return raw
  stack traces or ad-hoc shapes from controllers.
- **OpenAPI**: not wired up yet — `springdoc-openapi` compatibility with Spring Boot 4 needs
  verifying (latest indexed release at scaffold time was 2.8.6, predates Spring Boot 4). Check
  current compatibility before adding it in M2/M3.
- **Calling ml-service**: base URL from `ml-service.base-url` (env `ML_SERVICE_BASE_URL`).
  Forward the incoming `X-Correlation-Id` on every outgoing call.
