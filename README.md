<div align="center">

# myst

### Open-source claim verification

</div>

---

## What is myst?

**myst cross-validates environmental-based claims with pinpoint accuracy using a reverse-engineered methodology process** 


## Quickstart

```python
from myst.claim import Claim

claim = Claim(
    raw_text: str
    claim_type: Literal["forest_cover_loss"]
    value: float
    unit: float
    source: str | None = None
    magnitude: float
)
result = scenario.simulate(n_agents=500)

print(result.summary())  

```


## Installation

```bash
# From PyPI (once published)
pip install myst

# From source
git clone https://github.com/jadenryu/myst.git
cd myst
pip install -e ".[dev]"
```


Requires Python 3.11+ 


## Contributing

myst is pre-alpha. 

Open an issue or reach out on Gmail @ jadenryu@gmail.com!

## License

[Apache 2.0](LICENSE) - free to use, modify, and distribute commercially.
