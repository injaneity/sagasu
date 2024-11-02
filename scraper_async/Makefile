# Main entry target
all: start

# Start FastAPI application
start: save-keys-to-env
	@echo "Executing FastAPI & scraper async script..."
	source ../venv/bin/activate && python -m uvicorn api:app --reload

# Variables for filenames
PRIVATE_KEY_FILE=private_key.pem
PUBLIC_KEY_FILE=public_key.pem
ENV_FILE=.env

# Target to generate RSA keys
generate-keys:
	@echo "Generating RSA private and public keys..."
	@openssl genpkey -algorithm RSA -out $(PRIVATE_KEY_FILE) -pkeyopt rsa_keygen_bits:2048
	@openssl rsa -pubout -in $(PRIVATE_KEY_FILE) -out $(PUBLIC_KEY_FILE)

# Target to encode and save keys to .env
save-keys-to-env: generate-keys
	@echo "Encoding keys to base64..."
	@PRIVATE_KEY_B64=$$(openssl base64 -A -in $(PRIVATE_KEY_FILE)) && \
	PUBLIC_KEY_B64=$$(openssl base64 -A -in $(PUBLIC_KEY_FILE)) && \
	echo "PRIVATE_KEY=$$PRIVATE_KEY_B64" > $(ENV_FILE) && \
	echo "PUBLIC_KEY=$$PUBLIC_KEY_B64" >> $(ENV_FILE)
	@echo ".env file created with base64-encoded keys."

# Clean up generated files
clean:
	@rm -f $(PRIVATE_KEY_FILE) $(PUBLIC_KEY_FILE) $(ENV_FILE)
	@echo "Cleaned up generated files."
