import json

percentage_values = [5, 10, 15, 20]
use_gradient_values = [True, False]
use_ewma_values = [True, False]
model_values = ["LR", "SVM", "RF", "ET", "MLP", "AdaBoost", "DT", "DUM"]

for percentage in percentage_values:
    for use_gradient in use_gradient_values:
        for use_ewma in use_ewma_values:
            for model in model_values:
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

                filename = f"{model}_{percentage}_" \
                           f"{'grad' if use_gradient else 'no-grad'}_" \
                           f"{'ewma' if use_ewma else 'no-ewma'}" \
                           f".json"
                with open(filename, "w") as file:
                    json.dump(data, file, indent=4)

                print(f"Generated {filename}")
