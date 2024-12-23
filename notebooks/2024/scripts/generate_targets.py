import json
import itertools

percentage_values = list(range(1, 41))
use_gradient_values = [True, False]
use_ewma_values = [True, False]
use_scaling = [True, False]
model_values = ["LR", "SVM", "RF", "ET", "MLP", "AdaBoost", "DT", "DUM"]

# Define hyperparameters and their ranges
hyperparameters = {
    "LR": {"C": [0.1, 1.0, 10.0]},
    "SVM": {"C": [0.1, 1.0, 10.0], "kernel": ["linear", "rbf"]},
    "RF": {"n_estimators": [50, 100, 200], "max_depth": [None, 10, 20]},
    "ET": {"n_estimators": [50, 100, 200], "max_depth": [None, 10, 20]},
    "MLP": {"hidden_layer_sizes": [(10,), (20,), (10, 10)], "alpha": [0.0001, 0.001]},
    "AdaBoost": {"n_estimators": [50, 100, 200], "learning_rate": [0.1, 1.0]},
    "DT": {"max_depth": [None, 10, 20]},
}

# Generate all combinations of hyperparameters
hyperparameter_combinations = {}
for model in hyperparameters:
    hyperparameter_combinations[model] = list(itertools.product(*hyperparameters[model].values()))

for percentage_index, percentage in enumerate(percentage_values):
    for use_gradient_index, use_gradient in enumerate(use_gradient_values):
        for use_ewma_index, use_ewma in enumerate(use_ewma_values):
            # for use_scale_index, use_scale in enumerate(use_scaling):
            for model_index, model in enumerate(model_values):
                for hyper_i, hyperparams in enumerate(hyperparameter_combinations.get(model, [None])):
                    data = {
                        "percentage": percentage,
                        "use_gradient": use_gradient,
                        "use_ewma": use_ewma,
                        "model": model,
                        "k_fold": {
                            "n_splits": 10
                        },
                        "preprocessing": {
                            "scale": True,
                            "drop_constant_values": True
                        }
                    }

                    # Include hyperparameters in the data dictionary
                    if hyperparams:
                        data["hyperparameters"] = dict(zip(hyperparameters[model].keys(), hyperparams))
                    else:
                        data['hyperparameters'] = {}

                    filename = f"{model}_{percentage}_" \
                            f"{'grad' if use_gradient else 'no-grad'}_" \
                            f"{'ewma' if use_ewma else 'no-ewma'}"
                            # f"{'scale' if use_scale else 'no-scale'}" \

                    if hyperparams:
                        filename += f"_{hyper_i}"

                    filename += ".json"

                    with open(filename, "w") as file:
                        json.dump(data, file, indent=4)

                    print(f"Generated {filename}")
