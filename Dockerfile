FROM python:3.9-slim

WORKDIR /ama_app

COPY . /ama_app

# Install Rust and Cargo
RUN pip install -r requirements.txt

EXPOSE 1609

CMD ["uvicorn", "main_ama:app", "0.0.0.0", "--port", "1609:1609"]
