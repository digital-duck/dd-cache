import pickle


def serialize(value: object) -> bytes:
    return pickle.dumps(value)


def deserialize(data: bytes) -> object:
    return pickle.loads(data)


def make_key(*parts: str) -> str:
    return ":".join(parts)
