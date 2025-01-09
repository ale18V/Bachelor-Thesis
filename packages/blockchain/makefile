OUT_DIR=src/blockchain/generated
PROTO_DIR=proto

build:
	python3 -m grpc_tools.protoc --python_out=$(OUT_DIR) \
		--grpc_python_out=$(OUT_DIR) \
		--pyi_out=$(OUT_DIR)	\
		--proto_path=$(PROTO_DIR)/	\
		$(PROTO_DIR)/*.proto
	protol --create-package \
		--in-place \
		--python-out $(OUT_DIR)/ \
  		protoc --proto-path=$(PROTO_DIR)/ \
		--protoc-path "python3 -m grpcio_tools.protoc" \
		$(PROTO_DIR)/*.proto
