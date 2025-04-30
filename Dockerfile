FROM python:3.9-slim

WORKDIR /ama_app

COPY . /ama_app

# Install Rust and Cargo
RUN pip install -r requirements.txt

EXPOSE 2026

CMD ["uvicorn", "main_ama:app", "--host","0.0.0.0", "--port", "2026"]