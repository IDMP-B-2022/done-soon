Output samples from `minizinc`. `json` is prettified into lines here, but the real output is provided on a single line.

## Satisfy
Will finish with a single solution like the following.
```json
{
    "type": "solution",
    "output": {"default": "...", "raw": "..."},
    "sections": ["default", "raw"],
    "time": ###
}
```

## Min/Max
Will finish with both the solution and status message
```json
{
    "type": "solution",
    "output": {"default": "Objective = ...\n",
    "raw": "Objective = ...\n"},
    "sections": ["default", "raw"],
    "time": ###
}

{
    "type": "status",
    "status": "OPTIMAL_SOLUTION", 
    "time": ###
}
```

If the time limit is exceeded, the status message looks like this instead

```json
{
    "type": "status", 
    "status": "UNKNOWN", 
    "time": ###
}
```

## Statistics
Statistics keys are not necessarily correct.

```json
{
    "type": "statistics", 
    "statistics": 
        {
            "nodes": 85, 
            "failures": 65, 
            "restarts": 1, 
            "variables": 1904, 
            "intVars": 421, 
            "boolVariables": 1481, 
            "propagators": 116, 
            "propagations": 7163, 
            "peakDepth": 15, 
            "nogoods": 65, 
            "backjumps": 4, 
            "peakMem": 0.0, 
            "time": 0.006, 
            "initTime": 0.003, 
            "solveTime": 0.003, 
            "objective": 9, 
            "optTime": 0.003, 
            "baseMem": 0.0, 
            "trailMem": 0.04, 
            "randomSeed": 42
        }
    }
```