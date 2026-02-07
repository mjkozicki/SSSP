# Build and test SSSP TypeScript package
# Build context: repo root. Build: docker build -f docker/typescript/Dockerfile .

FROM node:22-alpine AS build
WORKDIR /src

# Cache npm install (re-run only when package*.json change)
COPY typescript/package.json typescript/package-lock.json* typescript/
WORKDIR /src/typescript
RUN npm ci 2>/dev/null || npm install

# Build and test
COPY typescript/ typescript/
RUN npm run build && npm test

# Minimal runtime (dist + node to run)
FROM node:22-alpine AS runtime
WORKDIR /app
COPY --from=build /src/typescript/dist/ dist/
COPY --from=build /src/typescript/package.json .
# CMD ["node", "-e", "const {duanMaoShuYin, Graph}=require('./dist'); ..."]
