# Use the official Playwright Python image as the base
FROM mcr.microsoft.com/playwright/python:v1.47.0-noble

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PLAYWRIGHT_BROWSERS_PATH=0

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's caching
COPY requirements.txt .

# Install Python dependencies, including Playwright
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Verify Playwright browsers are installed correctly
RUN ls -la /ms-playwright/chromium-1140/chrome-linux/ || echo "Chromium not found"

# Copy the rest of the application code
COPY . .

# Set ownership of the /app directory to pwuser
RUN chown -R pwuser:pwuser /app

RUN playwright install

# Switch to the non-root user
USER pwuser

# Generate RSA keys and create .env with base64-encoded keys
RUN openssl genpkey -algorithm RSA -out private_key.pem -pkeyopt rsa_keygen_bits:2048 && \
    openssl rsa -pubout -in private_key.pem -out public_key.pem && \
    PRIVATE_KEY_B64=$(openssl base64 -A -in private_key.pem) && \
    PUBLIC_KEY_B64=$(openssl base64 -A -in public_key.pem) && \
    echo "PRIVATE_KEY=${PRIVATE_KEY_B64}" > .env && \
    echo "PUBLIC_KEY=${PUBLIC_KEY_B64}" >> .env && \
    echo ".env file created with base64-encoded keys."

# Expose port 8000 for the FastAPI application
EXPOSE 8000

# Define the default command to run the FastAPI app with Uvicorn
CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
