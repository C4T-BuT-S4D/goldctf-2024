# Conveyor

Conveyor was a gold-related ML data and model pipeline "builder", allowing a client to generate randomized gold alloy datasets and then train simple linear models on the data using the features exposed via [RPyC](https://rpyc.readthedocs.io/en/latest/index.html). There were no intended vulnerabilities in the service code itself, and the intended exploitation method required using unreported 0day in the RPyC library source code to gain RCE via which flags from both redis and the filesystem could be exfiltrated.

## RPyC 0day

Despite the RPyC config containing `allow_pickle=False` by default ([rpyc@5.3.1/core/protocol.py#L63](https://github.com/tomerfiliba-org/rpyc/blob/ec5fbe51522cb6f31b43c346ba34b49b2b0dbeb6/rpyc/core/protocol.py#L63)), which does disable the pickling handler for objects ([rpyc@5.3.1/core/protocol.py#L899](https://github.com/tomerfiliba-org/rpyc/blob/ec5fbe51522cb6f31b43c346ba34b49b2b0dbeb6/rpyc/core/protocol.py#L899)), unpickling is still available through the `__array__` method, which is added specifically for transfer of numpy arrays across devices with different architectures ([rpyc@5.3.1/core/netref.py#L255](https://github.com/tomerfiliba-org/rpyc/blob/ec5fbe51522cb6f31b43c346ba34b49b2b0dbeb6/rpyc/core/netref.py#L255)).

Since the service contains a lot of logic which is directly related to working with pandas, sklearn, and numpy, it isn't difficult to find a location where this method would be used. As stated in the [numpy doc](https://numpy.org/doc/stable/reference/generated/numpy.array.html), `numpy.array` tries calling the `__array__` method during initialization, so `ModelConveyor`'s `fit_ridge` ([../../services/conveyor/conveyor/model.py#74](../../services/conveyor/conveyor/model.py#74)) method is perfect for this.

The vulnerability can be then be triggered using the described path by sending any object with the `__array__` method available. After discovering this method, the server will ask the client to pickle said object, which will directly call `pickle.dumps` on the object, so the classic `__reduce__` method is enough to create the exploit:

```python
class Exploit:
    def __init__(self, code: str):
        self.code = code

    def __array__(self):
        pass

    def __reduce__(self):
        return (__import__("builtins").eval, (self.code,))
```

The full exploit with flag exfiltration and some interesting traffic obfuscation methods can be seen here: [./conveyor-rpyc-0day.py](./conveyor-rpyc-0day.py). To launch it, run `poetry shell`, and then `python3 conveyor-rpyc-0day.py {ip} {account_id}`.
