The `done_soon` db will have a `problem` collection with documents that look like this:

```json
{
    "_id": "...",
    "mzn": "path/to/model.mzn",
    "dzn": "path/to/data.dzn",
    "generated_features": true,
    "generated_label": true,
    "claimed_features_generation": true,
    "claimed_label_generation": true,
    "type": "SAT",
    "time_to_solution": 1500,
    "time_limit": 72000000,

    "solved": true,
    "statistics": [
        {
            "percentage": 25.5,
            "features": {
                "one_stat": 0, "other_stat": 1}
        },
        {
            "percentage": 26.0,
            "features": {
                "one_stat": 1, "other_stat": 2}
        },
    ]
}
```