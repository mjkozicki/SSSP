# Docker images for SSSP

Each subfolder has a **Dockerfile** for that language. Build from the **repository root** so the build context includes the language folder.

## Build commands

From the repo root (`SSSP/`):

| Language    | Command |
|------------|---------|
| **C#**     | `docker build -f docker/csharp/Dockerfile .` |
| **Rust**   | `docker build -f docker/rust/Dockerfile .` |
| **C++**    | `docker build -f docker/cplusplus/Dockerfile .` |
| **Go**     | `docker build -f docker/go/Dockerfile .` |
| **Java**   | `docker build -f docker/java/Dockerfile .` |
| **PHP**    | `docker build -f docker/php/Dockerfile .` |
| **Python** | `docker build -f docker/python/Dockerfile .` |
| **TypeScript** | `docker build -f docker/typescript/Dockerfile .` |

## What each image does

- **Build** the project and **run tests** (or a quick sanity check for PHP).
- Use **multi-stage builds** where useful: build stage + smaller runtime stage (C#, Rust, C++, Go, Java, Python, TypeScript).
- **Cache** dependency layers (e.g. `COPY go.mod` then `go mod download`) so dependency steps only re-run when manifest files change.
- Use **Alpine or slim** bases where possible to keep image size down.

## Optional: tag and run

```bash
# Example: build and run C# tests
docker build -f docker/csharp/Dockerfile -t sssp-csharp .
docker run --rm sssp-csharp dotnet test /src/csharp/SSSP.Tests/SSSP.Tests.csproj -c Release --no-build -v minimal

# Example: run Go tests
docker build -f docker/go/Dockerfile -t sssp-go .
docker run --rm sssp-go go test -v ./...

# Example: run Java Main
docker build -f docker/java/Dockerfile -t sssp-java .
docker run --rm sssp-java java -cp /app/out sssp.Main
```
