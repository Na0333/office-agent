class PlatformService:
    def normalize_platform_name(self, platform: str) -> str:
        mapping = {
            "dingtalk": "钉钉",
            "wecom": "企业微信",
            "qq": "QQ",
            "web": "Web",
        }
        return mapping.get(platform, platform)

