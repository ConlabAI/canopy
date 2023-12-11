docker build -t canopy:latest . && docker run --env-file .env -p 127.0.0.1:8000:8000 canopy:latest 
