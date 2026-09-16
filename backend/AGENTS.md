@../AGENTS.md

## backend-specific conventions

- **Stack**: Java 21, Spring Boot 4.1.1, Maven. Use the system `mvn` — the generated `mvnw`
  wrapper tries to download its own Maven distribution and may fail without direct internet
  access to `repo.maven.apache.org`; prefer `mvn` directly in this environment.
- **Run**: `mvn spring-boot:run`. **Build/verify**: `mvn -q compile` or `mvn -q verify`.
- **Tests**: JUnit under `src/test/java`, mirroring the package under test. `mvn -q test`
  runs them (`mvn -q verify` runs tests as part of the build). **Needs a real Postgres
  running on `localhost:5432`** (matching `.env.example`'s defaults) — `BackendApplicationTests`
  boots the full Spring context, which runs Flyway on startup. Quickest way:
  `docker run -d -e POSTGRES_DB=cattlecare -e POSTGRES_USER=cattlecare -e POSTGRES_PASSWORD=cattlecare -p 5432:5432 postgres:16-alpine`,
  or just `make up` first. CI provides this as a service container (see `.github/workflows/ci.yml`).
- **DB migrations**: Flyway, `src/main/resources/db/migration/V<n>__description.sql`. Never
  edit a migration that may have already run — add a new one.
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
