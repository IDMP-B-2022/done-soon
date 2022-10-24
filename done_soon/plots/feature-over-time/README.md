# Data generation

The data generation system consists of three scripts: the initial database generator and a run_solver. This solver can be run independently of any other process of the same script, because of the synchronization via a SQLite3 database. The multicore.sh script just boots 16 processes, each with its own core allocated.

To get started, do the following:

* Go into the data-generation folder (so your current working directory is ./idm-2022/data_generation).
* Run create-initial-db.py
* Either run multicore.sh or run_solver.py
* and wait for results.
