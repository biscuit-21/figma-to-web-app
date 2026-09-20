BINARY  := key-indicators
VERSION := $(shell git describe --tags --always --dirty 2>/dev/null || echo dev)
LDFLAGS := -s -w -X main.version=$(VERSION)
PLATFORMS := linux/amd64 linux/arm64 darwin/amd64 darwin/arm64 windows/amd64

.PHONY: all build run data clean dist check

all: build

## build: compile the executable for this machine
build: web/index.html
	go build -trimpath -ldflags "$(LDFLAGS)" -o $(BINARY) .
	@echo "built ./$(BINARY) ($(VERSION))"

## run: build and start the dashboard
run: build
	./$(BINARY)

## data: rebuild web/index.html from tools/template.html + tools/data.json
data:
	python3 tools/build.py

web/index.html: tools/template.html tools/data.json
	python3 tools/build.py

## check: vet and compile without producing a binary
check: web/index.html
	go vet ./...
	go build -o /dev/null .

## dist: cross-compile release binaries into dist/
dist: web/index.html
	@rm -rf dist && mkdir -p dist
	@for p in $(PLATFORMS); do \
		os=$${p%/*}; arch=$${p#*/}; ext=""; \
		[ "$$os" = "windows" ] && ext=".exe"; \
		echo "  $$os/$$arch"; \
		GOOS=$$os GOARCH=$$arch CGO_ENABLED=0 \
		  go build -trimpath -ldflags "$(LDFLAGS)" \
		  -o dist/$(BINARY)-$$os-$$arch$$ext . || exit 1; \
	done
	@cd dist && sha256sum * > SHA256SUMS && cat SHA256SUMS

clean:
	rm -rf dist $(BINARY) $(BINARY).exe
