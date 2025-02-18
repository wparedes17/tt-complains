# TT-Complains Analysis Project

## Prerequisites

- Docker and Docker Compose
- Python 3.10 or higher
- pip (Python package installer)
- Git

## Setup Instructions

### 1. Database Setup

First, we'll set up the MySQL database using Docker:

```bash
# Navigate to the database directory
cd tt-complains/db

# Start the MySQL container
docker compose up -d
```

This will initialize a MySQL instance with the required configurations.

### 2. Python Environment Setup

After setting up the database, prepare your Python environment:

```bash
# Return to the project root directory
cd ../

# Install required Python packages
pip install -r requirements.txt
```

## Data Generation and Analysis

### 1. Generate Synthetic Data

Open and execute the `synthetic_data.ipynb` notebook:

```bash
jupyter notebook synthetic_data.ipynb
```

**Important**: 
- This notebook requires an active MySQL instance (started in step 1)
- Ensure the database connection is properly configured
- Execute all cells in sequential order

### 2. Exploratory Data Analysis and Modeling

Once the synthetic data is generated, proceed with the analysis:

```bash
jupyter notebook exploration_modelling.ipynb
```

**Dependencies**:
- Requires successful execution of `synthetic_data.ipynb`
- Uses the generated data from the MySQL database

## Troubleshooting

If you encounter any issues:

1. Ensure Docker containers are running:
   ```bash
   docker ps
   ```

2. Check MySQL connection:
   ```bash
   docker logs tt-complains-db
   ```

3. Verify Python package installation:
   ```bash
   pip list
   ```

## Notes

- The Docker setup uses the configuration specified in `docker-compose.yml`
- Default database credentials and configurations can be found in the database directory
- Make sure to check the requirements.txt file for specific package versions

## Contributing

Please refer to our contributing guidelines for information on how to propose changes or improvements to this project.