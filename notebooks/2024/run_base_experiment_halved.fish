for i in 1 2 3 4 5 6 7 8 9 10;
  python scripts/generate_pickles_for_base_experiment.py --input analysis/paper-data/all_features.pkl --output analysis/paper-data/base-experiment-halved-$i.pkl --random 60$i;
  # python scripts/cross_validate.py --target analysis/paper-data/targets_full --pickle analysis/paper-data/base-experiment-$i.pkl_train.pkl --output analysis/paper-data/cross-validations-base-experiment-$i;
end;

