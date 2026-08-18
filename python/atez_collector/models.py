from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class DocumentRef:
    title: str
    url: str
    filename: str

    def to_dict(self) -> dict:
        return asdict(self)
