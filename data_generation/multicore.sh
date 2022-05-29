# Does stuff

for VARIABLE in {1..15}
do
  echo $VARIABLE
  taskset -c $VARIABLE python run_solver.py &
done
