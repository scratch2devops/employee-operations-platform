FROM python:3.13-slim 
WORKDIR /app

#Create a non-root user 
RUN useradd --create-home --shell /bin/bash appuser

# Copy dependency definition first 
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy Application source
COPY src ./src

# Switch to non root user
USER appuser

EXPOSE 8000

CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
