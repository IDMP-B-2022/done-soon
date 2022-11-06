# Data Generation

The data generation process is centered around a single script [generate_data.py](generate_data.py). This script acts as a controller and spawns processes which run the [data_gen_worker.py](data_gen_worker.py) script. The worker pulls problems to solve from the database and uses `solve_problem.py` to launch `minizinc` to solve them. The worker then stores the output in the database. If the woerker/solver dies for some reason, the controller will spawn a new worker within 10s. When there are no problems left in the database, the controller will continue to spawn workers. The user must terminate the process when they deem it completed. Note that the user can insert new problems to the datbase on the fly. The workers will pick them up as they arrive.


### The Easy Way (Docker)
The easiest way to carry out the data generation is via `docker compose`. As long as you have `docker compose` [installed](https://docs.docker.com/compose/install/), then running `docker compose up` will build everything, create and populate the database, and run each of the problems in the database to create the data.


### Manual Install/Run
If you want to run the process directly on your own system, you'll have to make sure all of the required software, datasets, etc are downloaded/installed. See the main README for instructions. Once all prerequisites are met, you'll just need to run the database generation script ([db/scripts/create_initial_db.py](db/scripts/create_initial_db.py)), and then the [generate_data.py](generate_data.py) script.
