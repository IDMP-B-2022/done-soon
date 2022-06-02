# Does stuff

for VARIABLE in {0..8}
do
  echo $VARIABLE
  taskset -c $VARIABLE python3 run_solver.py &
  sleep 1
done
