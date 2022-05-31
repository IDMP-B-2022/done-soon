# Does stuff

for VARIABLE in {0..8}
do
  echo $VARIABLE
  taskset -c $VARIABLE python run_solver.py &
done
