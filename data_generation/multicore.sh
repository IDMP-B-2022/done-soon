# Runs a number of solver instances
# Takes as an argument, the mode to run the solver in. Either `label` or `features`

for VARIABLE in {0..8}
do
  echo $VARIABLE
  taskset -c $VARIABLE python3 run_solver.py --mode $1 &
  sleep 1
done
