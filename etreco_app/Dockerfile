# Use an official Python runtime as a parent image
FROM python:latest

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -U pip wheel
RUN pip install --no-cache-dir -r requirements.txt

# Run app.py when the container launches
CMD ["python", "recommend.py", ">stdout", "2>stderr"]
