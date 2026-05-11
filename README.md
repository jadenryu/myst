## lurq

open-source simulation engine, simulating what happens when you change a policy, tariff or regulation.

**Status:** v0 in active development, star to follow!

## Quickstart

​```python
import lurq

scenario = lurq.Scenario(
    domain="labor_economics",
    region="California",
    policy=lurq.Policy(
        variable="min_wage_fast_food",
        from_value=16.0,
        to_value=22.0,
    ),
    horizon_months=24,
)

result = scenario.simulate(n_agents=500)
print(result.summary())
​```

## License

Apache 2.0
