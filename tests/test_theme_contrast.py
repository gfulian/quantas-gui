from __future__ import annotations


def _luminance(value: str) -> float:
    channels = [int(value[index : index + 2], 16) / 255.0 for index in (1, 3, 5)]
    linear = [
        channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4
        for channel in channels
    ]
    return 0.2126 * linear[0] + 0.7152 * linear[1] + 0.0722 * linear[2]


def _contrast(first: str, second: str) -> float:
    bright, dark = sorted((_luminance(first), _luminance(second)), reverse=True)
    return (bright + 0.05) / (dark + 0.05)


def test_core_dark_and_light_text_tokens_meet_normal_text_contrast() -> None:
    dark_background = "#071522"
    for foreground in ("#ecf5fb", "#b3c7d5", "#7f9bad"):
        assert _contrast(foreground, dark_background) >= 4.5

    light_background = "#f3f7fa"
    for foreground in ("#142b3a", "#365365", "#58717f"):
        assert _contrast(foreground, light_background) >= 4.5


def test_control_and_payload_surfaces_remain_readable_in_both_themes() -> None:
    dark_control = "#04101a"
    for foreground in ("#ecf5fb", "#b3c7d5", "#7f9bad"):
        assert _contrast(foreground, dark_control) >= 4.5

    light_control = "#ffffff"
    for foreground in ("#142b3a", "#365365", "#58717f"):
        assert _contrast(foreground, light_control) >= 4.5

    light_payload = "#f4f8fb"
    assert _contrast("#365365", light_payload) >= 4.5
