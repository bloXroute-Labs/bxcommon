from typing import NamedTuple, Optional


class SSLFileInfo(NamedTuple):
    sub_directory_name: str
    file_name: str
    url: Optional[str] = None

    def __repr__(self) -> str:
        return f"{self.__class__.__name__} <" \
            f"sub_directory_name = {self.sub_directory_name}, " \
            f"file_name = {self.file_name}, " \
            f"url = {self.url}" \
            f">"
