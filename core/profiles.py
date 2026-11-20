import os
import json
from dataclasses import asdict
from typing import List
from core.models import AppProfile


class ProfileManager:
    """Хранение и загрузка профилей настроек пользователя."""

    def __init__(self, base_dir: str = ""):
        if not base_dir:
            base_dir = os.path.join(os.path.expanduser("~"), ".context_builder_profiles")
        self.base_dir = base_dir
        os.makedirs(self.base_dir, exist_ok=True)

    def _path_for(self, name: str) -> str:
        safe = "".join(c for c in name if c.isalnum() or c in ("-", "_", " ")).strip()
        return os.path.join(self.base_dir, f"{safe}.json")

    def list_profiles(self) -> List[str]:
        if not os.path.isdir(self.base_dir):
            return []
        names = []
        for fn in sorted(os.listdir(self.base_dir)):
            if fn.endswith(".json"):
                names.append(fn[:-5])
        return names

    def save_profile(self, profile: AppProfile) -> str:
        path = self._path_for(profile.name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(asdict(profile), f, ensure_ascii=False, indent=2)
        return path

    def load_profile(self, name: str) -> AppProfile:
        path = self._path_for(name)
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return AppProfile(**data)

    def delete_profile(self, name: str) -> bool:
        path = self._path_for(name)
        if os.path.isfile(path):
            os.remove(path)
            return True
        return False