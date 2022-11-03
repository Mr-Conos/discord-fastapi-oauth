from typing import Dict, List, Optional

from .. import constants as const


class Guild:

    def __init__(self, payload: Dict):
        self.id = int(payload["id"])
        self.name: str = payload["name"]
        self.icon_hash: Optional[str] = payload.get("icon")
        self.owner: bool = payload["owner"]
        self.permissions = int(payload["permissions"])
        self.features: List[str] = payload["features"]

    @property
    def icon_url(self) -> Optional[str]:
        if not self.icon_hash:
            return None

        image_format = const.DISCORD_ANIMATED_IMAGE_FORMAT if self.is_icon_animated else const.DISCORD_IMAGE_FORMAT

        return const.DISCORD_GUILD_ICON_BASE_URL.format(guild_id=self.id, icon_hash=self.icon_hash, format=image_format)

    @property
    def is_icon_animated(self) -> bool:
        return self.icon_hash and self.icon_hash.startswith("a_")


class User:

    def __init__(self, payload: Dict):
        self.id = int(payload["id"])
        self.username: str = payload["username"]
        self.discriminator: str = payload["discriminator"]
        self.avatar_hash: Optional[str] = payload.get("avatar")

        self._guilds: Dict[int, Guild] = None  # type: ignore

    @property
    def guilds(self) -> Optional[List[Guild]]:
        if not self._guilds:
            return None

        return list(self._guilds.values())

    @guilds.setter
    def guilds(self, value):
        self._guilds = value

    @property
    def avatar_url(self) -> str:
        image_format = const.DISCORD_ANIMATED_IMAGE_FORMAT if self.is_avatar_animated else const.DISCORD_IMAGE_FORMAT

        if not self.avatar_hash:
            return const.DISCORD_DEFAULT_USER_AVATAR_BASE_URL.format(modulo5=int(self.discriminator) % 5)

        return const.DISCORD_USER_AVATAR_BASE_URL.format(
            user_id=self.id, avatar_hash=self.avatar_hash, format=image_format
        )

    @property
    def is_avatar_animated(self) -> bool:
        return self.avatar_hash and self.avatar_hash.startswith("a_")
