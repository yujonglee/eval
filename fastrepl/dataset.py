from typing import Optional, Callable, Literal, Dict, List, Any, cast

import httpx

import fastrepl
import fastrepl.llm as llm
from fastrepl.errors import DatasetPushError


class Dataset:
    __slots__ = ("_data", "_iter")

    def __init__(self) -> None:
        self._data: Dict[str, List[Any]] = {}

    def __repr__(self) -> str:
        return f"fastrepl.Dataset({{\n    features: {self.column_names},\n    num_rows: {self.__len__()}\n}})"

    def __len__(self) -> int:
        v0: List[Any] = next(iter(self._data.values()), [])
        return len(v0)

    def __getitem__(self, key: str) -> List[Any]:
        if key in self._data:
            return self._data[key]
        else:
            raise KeyError

    def __iter__(self):
        key = list(self._data.keys())[0]
        self._iter = range(len(self._data[key])).__iter__()
        return self

    def __next__(self) -> Dict[str, Any]:
        try:
            i = next(self._iter)
            return {col: self._data[col][i] for col in self.column_names}
        except StopIteration:
            raise StopIteration

    @property
    def column_names(self) -> List[str]:
        return list(self._data.keys())

    def add_column(self, name: str, values: List[Any]) -> "Dataset":
        if self.__len__() != len(values):
            raise ValueError

        self._data[name] = list(values)
        return self

    def add_row(self, row: Dict[str, Any]):
        for col in self.column_names:
            if col not in row:
                row[col] = None

        existing_size = self.__len__()

        for k, v in row.items():
            try:
                self._data[k].append(v)
            except KeyError:
                self._data[k] = [None] * existing_size
                self._data[k].append(v)

    def rename_column(self, old_name: str, new_name: str) -> "Dataset":
        data = {col: self._data[col] for col in self.column_names}
        data[new_name] = data.pop(old_name)
        return Dataset.from_dict(data)

    def remove_column(self, name: str) -> "Dataset":
        data = {col: self._data[col] for col in self.column_names}
        del data[name]
        return Dataset.from_dict(data)

    def clear(self):
        self._data = {}

    def map(self, func: Callable[[Dict[str, Any]], Dict[str, Any]]) -> "Dataset":
        rows = []
        for row in self:
            rows.append(func(row))
        data = {col: [row[col] for row in rows] for col in self.column_names}
        return Dataset.from_dict(data)

    @classmethod
    def _headers(cls):
        return {"Authorization": f"Bearer {fastrepl.api_key}"}

    @classmethod
    def _base_url(cls):
        return f"{fastrepl.api_base}/dataset"

    @classmethod
    def from_dict(cls, data: Dict[str, List[Any]]) -> "Dataset":
        size = len(next(iter(data.values()), []))
        for value in data.values():
            if len(value) != size:
                raise ValueError

        ds = Dataset()
        ds._data = data
        return ds

    def to_dict(self) -> Dict[str, List[Any]]:
        return self._data

    @classmethod
    def from_hf(cls, data: Any) -> "Dataset":
        from datasets import Dataset as HF_Dataset

        hf_ds = cast(HF_Dataset, data)

        ds = Dataset()
        ds._data = hf_ds.to_dict()
        return ds

    def to_hf(self):
        from datasets import Dataset as HF_Dataset

        return HF_Dataset.from_dict(self._data)

    @classmethod
    def from_cloud(cls, id: str, version: Optional[str] = None) -> "Dataset":
        if fastrepl.api_key is None or fastrepl.api_base is None:
            raise ValueError

        url = f"{Dataset._base_url()}/get/{id}"
        if version is not None:
            url += f"?version={version}"

        with httpx.Client(headers=Dataset._headers()) as client:
            res = client.get(url).json()
            data = res["data"]

            return Dataset.from_dict(data)

    @classmethod
    def list_cloud(cls) -> List[str]:
        if fastrepl.api_key is None or fastrepl.api_base is None:
            raise ValueError

        url = f"{Dataset._base_url()}/list"

        with httpx.Client(headers=Dataset._headers()) as client:
            res = client.get(url)
            return res.json()["ids"]

    def push_to_cloud(self, id: Optional[str]) -> str:
        if fastrepl.api_key is None or fastrepl.api_base is None:
            raise ValueError

        url = f"{Dataset._base_url()}/new"

        with httpx.Client(headers=Dataset._headers()) as client:
            res = client.post(url, json={"id": id, "data": self._data})

            try:
                return res.json()["id"]
            except Exception as e:
                raise DatasetPushError(res)

    @classmethod
    def from_langfuse(cls, data: Any) -> "Dataset":
        from langfuse.client import DatasetClient as LF_Dataset

        lf_ds = cast(LF_Dataset, data)

        PREFIX = "_lf"

        data = {
            f"{PREFIX}_item_index": [],
            "inputs": [],
            "expected_outputs": [],
        }

        for i, item in enumerate(lf_ds.items):
            data[f"{PREFIX}_item_index"].append(i)
            data["inputs"].append(item.input)
            data["expected_outputs"].append(item.expected_output)

        return Dataset.from_dict(data)

    def compare(
        self,
        metric_name: Literal["accuracy", "mse", "mae"],
        prediction_column="prediction",
        reference_column="reference",
    ):
        metric = fastrepl.load_metric(metric_name)

        try:
            predictions = self._data[prediction_column]
            references = self._data[reference_column]
        except KeyError as e:
            raise ValueError(f"Column not found: {e}")

        return metric.run(predictions=predictions, references=references)

    def augment(self, multiple=3, model="gpt-4"):
        import json

        for row in self:
            sample = {k: [v] for k, v in row.items()}

            res = llm.completion(
                model=model,
                temperature=0.5,
                messages=[
                    {
                        "role": "system",
                        "content": "You are helpful assistant who can generate correct JSON string.",
                    },
                    {
                        "role": "user",
                        "content": f"Here's current sample:\n```json\n{json.dumps(sample)}```\nNow, give me same format but has {multiple} items per field. It should not be duplicated with current sample.\n\n```json\n",
                    },
                ],
                stop=["```"],
            )
            text = res["choices"][0]["message"]["content"]

            try:
                data: dict = json.loads(text)

                for row in [
                    dict(zip(data.keys(), values)) for values in zip(*data.values())
                ]:
                    self.add_row(row)

            except Exception:
                continue
