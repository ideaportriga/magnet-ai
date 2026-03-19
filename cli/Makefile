CLI_VERSION ?= $(shell git describe --tags --always --dirty 2>/dev/null || echo "dev")
BUILD_FLAGS  = -ldflags="-s -w -X main.version=$(CLI_VERSION)"
BINARY       = bin/magnet

.PHONY: build build-all install lint test clean

build:
	go build $(BUILD_FLAGS) -o $(BINARY) ./

build-all:
	mkdir -p dist
	GOOS=linux   GOARCH=amd64  go build $(BUILD_FLAGS) -o dist/magnet-linux-amd64 ./
	GOOS=linux   GOARCH=arm64  go build $(BUILD_FLAGS) -o dist/magnet-linux-arm64 ./
	GOOS=darwin  GOARCH=amd64  go build $(BUILD_FLAGS) -o dist/magnet-darwin-amd64 ./
	GOOS=darwin  GOARCH=arm64  go build $(BUILD_FLAGS) -o dist/magnet-darwin-arm64 ./
	GOOS=windows GOARCH=amd64  go build $(BUILD_FLAGS) -o dist/magnet-windows-amd64.exe ./

install:
	go install $(BUILD_FLAGS) ./

lint:
	go vet ./...
	@if command -v golangci-lint > /dev/null; then golangci-lint run ./...; fi

test:
	go test ./... -v

clean:
	rm -rf bin/ dist/

run:
	go run ./ $(ARGS)
